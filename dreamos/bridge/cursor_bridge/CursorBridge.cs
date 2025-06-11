using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Automation;
using System.Text.Json;
using System.Collections.Generic;

namespace DreamOS.Bridge
{
    public class CursorBridge
    {
        private readonly string _outputPath;
        private readonly CancellationTokenSource _cts;
        private AutomationElement _cursorWindow;
        private AutomationElement _responsePanel;
        private string _lastResponse;

        public CursorBridge(string outputPath)
        {
            _outputPath = outputPath;
            _cts = new CancellationTokenSource();
            _lastResponse = string.Empty;
        }

        public async Task StartAsync()
        {
            try
            {
                // Find Cursor window
                _cursorWindow = FindCursorWindow();
                if (_cursorWindow == null)
                {
                    throw new Exception("Cursor window not found");
                }

                // Find response panel
                _responsePanel = FindResponsePanel(_cursorWindow);
                if (_responsePanel == null)
                {
                    throw new Exception("Response panel not found");
                }

                // Start monitoring for changes
                await MonitorResponseChangesAsync(_cts.Token);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error in CursorBridge: {ex.Message}");
                throw;
            }
        }

        public void Stop()
        {
            _cts.Cancel();
        }

        private AutomationElement FindCursorWindow()
        {
            // Find window by title containing "Cursor"
            var root = AutomationElement.RootElement;
            var condition = new PropertyCondition(
                AutomationElement.NameProperty,
                "Cursor",
                PropertyConditionFlags.IgnoreCase
            );

            return root.FindFirst(TreeScope.Children, condition);
        }

        private AutomationElement FindResponsePanel(AutomationElement window)
        {
            // Find the response panel by its automation ID or class name
            // This will need to be updated based on Cursor's actual UI structure
            var condition = new PropertyCondition(
                AutomationElement.ClassNameProperty,
                "CodeMirror" // Example - update with actual class name
            );

            return window.FindFirst(TreeScope.Descendants, condition);
        }

        private async Task MonitorResponseChangesAsync(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                try
                {
                    var currentText = GetResponseText();
                    if (currentText != _lastResponse)
                    {
                        _lastResponse = currentText;
                        await SaveResponseAsync(currentText);
                    }

                    await Task.Delay(100, ct); // Poll every 100ms
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"Error monitoring response: {ex.Message}");
                }
            }
        }

        private string GetResponseText()
        {
            if (_responsePanel == null) return string.Empty;

            // Get the text content from the response panel
            var pattern = _responsePanel.GetCurrentPattern(ValuePattern.Pattern) as ValuePattern;
            if (pattern != null)
            {
                return pattern.Current.Value;
            }

            // Fallback to TextPattern if ValuePattern not available
            var textPattern = _responsePanel.GetCurrentPattern(TextPattern.Pattern) as TextPattern;
            if (textPattern != null)
            {
                return textPattern.DocumentRange.GetText(-1);
            }

            return string.Empty;
        }

        private async Task SaveResponseAsync(string response)
        {
            var responseData = new
            {
                timestamp = DateTime.UtcNow,
                content = response,
                source = "cursor"
            };

            var json = JsonSerializer.Serialize(responseData, new JsonSerializerOptions
            {
                WriteIndented = true
            });

            await File.WriteAllTextAsync(_outputPath, json);
        }
    }
} 