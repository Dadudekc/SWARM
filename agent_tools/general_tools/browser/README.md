# Stealth Browser Automation Tool

A powerful, modular browser automation tool designed for seamless interaction with web applications, particularly optimized for OpenAI's Codex platform. This tool enables automated login, session management, and direct interaction with web interfaces through a robust, stealth-enabled browser instance.

## 🌟 Key Features

### 1. Smart Authentication
- **Cookie-Based Session Management**
  - Automatic cookie persistence and reuse
  - Session restoration without manual login
  - Secure cookie storage and validation

- **Multi-Step Login Handling**
  - Intelligent detection of login elements
  - Support for email/password authentication
  - Verification code handling
  - Robust error recovery

### 2. Stealth Capabilities
- **Anti-Detection Measures**
  - Browser fingerprint randomization
  - User agent rotation
  - Natural interaction patterns
  - Timing randomization

### 3. Interactive Debugging
- **Real-Time Inspection**
  - Page element analysis
  - DOM structure inspection
  - Form element detection
  - Hotkey-based interaction

### 4. Codex Integration
- **Direct Message Interface**
  - Automated message input
  - Response detection
  - Code block handling
  - Markdown parsing

## 🛠️ Technical Architecture

### Core Components

1. **StealthBrowser**
   - Main browser instance management
   - Configuration handling
   - Resource cleanup

2. **LoginHandler**
   - Authentication flow management
   - Element detection and interaction
   - Session verification

3. **CookieManager**
   - Cookie persistence
   - Session restoration
   - Security validation

4. **DebugHelper**
   - Interactive debugging
   - Element inspection
   - Page analysis

## 🤖 Swarm Use Cases

### 1. Automated Code Review
```python
# Example: Automated code review workflow
browser = StealthBrowser(config)
browser.login_handler.input_codex_message("Review this code for security vulnerabilities:")
# Swarm agents can analyze responses and provide feedback
```

### 2. Quality Assurance
- Automated testing of web interfaces
- Cross-browser compatibility checks
- Performance monitoring
- Accessibility validation

### 3. Content Generation
- Automated documentation creation
- Code snippet generation
- API documentation
- Test case generation

### 4. Security Analysis
- Automated security scanning
- Vulnerability assessment
- Penetration testing
- Security compliance checks

### 5. Development Workflow
- Automated deployment verification
- Environment testing
- Configuration validation
- Integration testing

## 🚀 Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from agent_tools.general_tools.browser import StealthBrowser, DEFAULT_CONFIG

# Initialize browser
browser = StealthBrowser(DEFAULT_CONFIG)

# Start session
browser.start()

# Send message to Codex
browser.login_handler.input_codex_message("Your message here")

# Wait for response
browser.login_handler.wait_for_codex_response()
```

### Interactive Mode
```bash
python -m agent_tools.general_tools.browser
```

## 🔧 Configuration

### Key Settings
```python
DEFAULT_CONFIG = {
    'headless': False,
    'window_size': (1920, 1080),
    'page_load_wait': 30,
    'element_wait': 10,
    'cookies_file': 'cookies.json',
    'credentials': {
        'email': 'your-email@example.com',
        'password': 'your-password'
    }
}
```

## 🔍 Advanced Features

### 1. Element Detection
- Multiple selector strategies
- Fallback mechanisms
- Dynamic element waiting
- Error recovery

### 2. Session Management
- Automatic cookie refresh
- Session persistence
- Security validation
- Error handling

### 3. Debugging Tools
- Interactive hotkeys
- Element inspection
- Page analysis
- Response monitoring

## 🛡️ Security Considerations

1. **Credential Management**
   - Secure storage
   - Encryption
   - Access control

2. **Session Security**
   - Cookie validation
   - Session timeout
   - Access logging

3. **Resource Cleanup**
   - Automatic cleanup
   - Memory management
   - File handling

## 🔄 Integration Examples

### 1. CI/CD Pipeline
```python
def verify_deployment():
    browser = StealthBrowser(config)
    browser.login_handler.verify_login()
    # Add deployment verification logic
```

### 2. Automated Testing
```python
def run_security_scan():
    browser = StealthBrowser(config)
    browser.login_handler.input_codex_message("Scan this code for security issues:")
    # Process security scan results
```

### 3. Documentation Generation
```python
def generate_docs():
    browser = StealthBrowser(config)
    browser.login_handler.input_codex_message("Generate documentation for this API:")
    # Process and format documentation
```

## 📈 Performance Optimization

1. **Resource Management**
   - Memory optimization
   - CPU usage control
   - Network efficiency

2. **Response Time**
   - Element wait optimization
   - Page load handling
   - Network latency management

3. **Error Recovery**
   - Automatic retry
   - Fallback mechanisms
   - Error logging

## 🔮 Future Enhancements

1. **AI Integration**
   - Advanced pattern recognition
   - Natural language processing
   - Automated decision making

2. **Scalability**
   - Multi-instance support
   - Load balancing
   - Resource optimization

3. **Extended Features**
   - Additional platform support
   - Enhanced debugging
   - Advanced automation

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for more information.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 