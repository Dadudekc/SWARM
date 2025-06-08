import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

import Redis from 'ioredis';

// Configuration interfaces
interface RedisConfig {
    host: string;
    port: number;
    password: string;
    db: number;
}

interface OutboxConfig {
    path: string;
    archivePath: string;
    maxAgeDays: number;
}

interface MarkerConfig {
    end: string;
    error: string;
    warning: string;
    success: string;
}

interface FilteringConfig {
    ignoreMarkers: boolean;
    ignorePrompts: boolean;
    ignoreEmptyLines: boolean;
    redactPatterns: string[];
}

// Extension state
let redisClient: Redis | null = null;
let responseBuffer: string = '';
let lastPublishedResponse: string = '';
let currentAgentId: string | null = null;

// Helper functions
function getConfig<T>(section: string): T {
    return vscode.workspace.getConfiguration('dreamos').get(section) as T;
}

function getRedisConfig(): RedisConfig {
    return getConfig<RedisConfig>('redis');
}

function getOutboxConfig(): OutboxConfig {
    return getConfig<OutboxConfig>('outbox');
}

function getMarkerConfig(): MarkerConfig {
    return getConfig<MarkerConfig>('markers');
}

function getFilteringConfig(): FilteringConfig {
    return getConfig<FilteringConfig>('filtering');
}

function initializeRedis(): void {
    const config = getRedisConfig();
    redisClient = new Redis({
        host: config.host,
        port: config.port,
        password: config.password || undefined,
        db: config.db
    });
}

function ensureOutboxDirectories(): void {
    const config = getOutboxConfig();
    if (!fs.existsSync(config.path)) {
        fs.mkdirSync(config.path, { recursive: true });
    }
    if (!fs.existsSync(config.archivePath)) {
        fs.mkdirSync(config.archivePath, { recursive: true });
    }
}

function filterResponse(content: string): string {
    const config = getFilteringConfig();
    let filtered = content;

    if (config.ignoreMarkers) {
        const markers = getMarkerConfig();
        Object.values(markers).forEach(marker => {
            filtered = filtered.replace(new RegExp(`^${marker}$`, 'gm'), '');
        });
    }

    if (config.ignorePrompts) {
        filtered = filtered.replace(/^>.*$/gm, '');
    }

    if (config.ignoreEmptyLines) {
        filtered = filtered.replace(/^\s*[\r\n]/gm, '');
    }

    config.redactPatterns.forEach(pattern => {
        filtered = filtered.replace(new RegExp(pattern, 'g'), '[REDACTED]');
    });

    return filtered.trim();
}

function publishResponse(content: string): void {
    if (!redisClient || !currentAgentId) {
        return;
    }

    const filteredContent = filterResponse(content);
    const response = {
        agentId: currentAgentId,
        content: filteredContent,
        timestamp: new Date().toISOString()
    };

    // Publish to Redis
    redisClient.publish('agent-responses', JSON.stringify(response));

    // Write to outbox
    const config = getOutboxConfig();
    const filename = `${currentAgentId}_${Date.now()}.json`;
    fs.writeFileSync(
        path.join(config.path, filename),
        JSON.stringify(response, null, 2)
    );

    lastPublishedResponse = filteredContent;
    responseBuffer = '';
}

// Command handlers
function handleFlushBuffer(): void {
    if (responseBuffer) {
        publishResponse(responseBuffer);
        vscode.window.showInformationMessage('Response buffer flushed');
    }
}

function handleForceEnd(): void {
    if (responseBuffer) {
        publishResponse(responseBuffer);
        vscode.window.showInformationMessage('Response force-ended');
    }
}

function handleShowLastResponse(): void {
    if (lastPublishedResponse) {
        const doc = vscode.workspace.openTextDocument({
            content: lastPublishedResponse,
            language: 'markdown'
        });
        doc.then(d => vscode.window.showTextDocument(d));
    } else {
        vscode.window.showInformationMessage('No response has been published yet');
    }
}

// Document change handler
function handleDocumentChange(event: vscode.TextDocumentChangeEvent): void {
    const doc = event.document;
    const filename = path.basename(doc.fileName);
    
    // Check if this is an agent document
    const match = filename.match(/^agent-(\d+)\.md$/);
    if (!match) {
        return;
    }

    currentAgentId = `agent-${match[1]}`;
    const markers = getMarkerConfig();

    // Check for end marker
    const content = doc.getText();
    if (content.includes(markers.end)) {
        publishResponse(content);
        vscode.window.showInformationMessage(`Response from ${currentAgentId} published`);
    } else {
        responseBuffer = content;
    }
}

// Extension activation
export function activate(context: vscode.ExtensionContext): void {
    console.log('Dream.OS Agent Capture extension is now active');

    // Initialize Redis and outbox
    initializeRedis();
    ensureOutboxDirectories();

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('dreamos.flushBuffer', handleFlushBuffer),
        vscode.commands.registerCommand('dreamos.forceEnd', handleForceEnd),
        vscode.commands.registerCommand('dreamos.showLastResponse', handleShowLastResponse)
    );

    // Register document change handler
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(handleDocumentChange)
    );

    // Register configuration change handler
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('dreamos.redis')) {
                initializeRedis();
            }
            if (e.affectsConfiguration('dreamos.outbox')) {
                ensureOutboxDirectories();
            }
        })
    );
}

// Extension deactivation
export function deactivate(): void {
    if (redisClient) {
        redisClient.quit();
    }
} 