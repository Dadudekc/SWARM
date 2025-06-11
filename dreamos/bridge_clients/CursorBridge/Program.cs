using System;
using System.IO;
using CursorBridge.bridge;

namespace CursorBridge;

class Program
{
    static void Main(string[] args)
    {
        string response = ResponseExtractor.CaptureResponse();

        string outputPath = Path.Combine(Directory.GetCurrentDirectory(), "cursor_response.json");

        var json = $"{{\"response\": \"{response}\"}}";
        File.WriteAllText(outputPath, json);

        Console.WriteLine("Response written to: " + outputPath);
    }
}

public class BridgeCommand
{
    public string? Action { get; set; }
}
