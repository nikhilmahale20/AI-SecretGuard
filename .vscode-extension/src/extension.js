"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.NeuralSentinelFixer = void 0;
exports.activate = activate;
exports.deactivate = deactivate;
// extension.ts
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
// Create a global diagnostic collection for Neural-Sentinel
const diagnosticCollection = vscode.languages.createDiagnosticCollection("neuralSentinel");
function activate(context) {
    // Command 1: The Global Installer (Sets up the Git Hook)
    let setupDisposable = vscode.commands.registerCommand('neural-sentinel.setupGlobal', () => {
        const terminal = vscode.window.createTerminal("Neural-Sentinel Setup");
        terminal.show();
        const scriptPath = path.join(context.extensionPath, 'scripts', 'global_installer.py');
        terminal.sendText(`python "${scriptPath}"`);
        vscode.window.showInformationMessage("✅ Neural-Sentinel: Initializing Global Guardian...");
    });
    // Command 2: The AI Scan & Diagnostic Generator (With Timeout & Safe Indexing)
    let scanDisposable = vscode.commands.registerCommand('neural-sentinel.scanFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const document = editor.document;
        const text = document.getText();
        const fileName = path.basename(document.fileName);
        vscode.window.showInformationMessage("🧠 Neural-Sentinel: Analyzing Context Flow...");
        // 30-second timeout so the AI has time to think
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        try {
            const response = await fetch('http://127.0.0.1:8000/scan-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_name: fileName, code_content: text }),
                signal: controller.signal // Link the timeout signal
            });
            clearTimeout(timeoutId); // Cancel the timeout if the server responds
            const data = await response.json();
            diagnosticCollection.clear();
            if (data.status === "danger" && data.threats && data.threats.length > 0) {
                const diagnostics = [];
                data.threats.forEach((threat) => {
                    // 1. Safe Line Indexing
                    const lineIndex = Math.max(0, threat.line - 1);
                    // 2. Prevent IndexOutOfBounds Crash
                    if (lineIndex >= document.lineCount)
                        return;
                    const lineText = document.lineAt(lineIndex).text;
                    // 3. Search for the variable name on that line AND nearby lines
                    let finalLine = lineIndex;
                    let startIndex = lineText.indexOf(threat.variable_name);
                    if (startIndex === -1 && lineIndex > 0) {
                        // Check one line above if not found
                        const prevLine = document.lineAt(lineIndex - 1).text;
                        if (prevLine.indexOf(threat.variable_name) !== -1) {
                            finalLine = lineIndex - 1;
                            startIndex = prevLine.indexOf(threat.variable_name);
                        }
                    }
                    // 4. Fallback: Highlight the whole line if exact string isn't found
                    const startPos = startIndex !== -1 ? startIndex : 0;
                    const endPos = startIndex !== -1 ? startIndex + threat.variable_name.length : lineText.length;
                    const range = new vscode.Range(finalLine, startPos, finalLine, endPos);
                    const diagnostic = new vscode.Diagnostic(range, `🛑 AI Alert: Obfuscated secret detected (Confidence: ${(threat.confidence * 100).toFixed(1)}%)`, vscode.DiagnosticSeverity.Error);
                    diagnostic.code = { value: "extract-to-env", target: vscode.Uri.parse(threat.secret_value) };
                    diagnostics.push(diagnostic);
                });
                diagnosticCollection.set(document.uri, diagnostics);
                vscode.window.showWarningMessage(`⚠️ Neural-Sentinel: Found ${data.threats.length} potential secrets!`);
            }
            else {
                vscode.window.showInformationMessage("✅ Neural-Sentinel AI: Code flow is secure.");
            }
        }
        catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                vscode.window.showErrorMessage("❌ Neural-Sentinel: AI Scan timed out. The file is too complex or the server is slow.");
            }
            else {
                console.error("Extension Error:", error);
                vscode.window.showErrorMessage("❌ Connection Failed: Is your FastAPI Python server running on port 8000?");
            }
        }
    });
    // Command 3: The Auto-Remediator (Creates .env and updates .gitignore)
    let appendToEnvDisposable = vscode.commands.registerCommand('neural-sentinel.appendToEnv', async (varName, secretValue) => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage("Neural-Sentinel: Please open a workspace folder to create a .env file.");
            return;
        }
        const envPath = path.join(workspaceFolders[0].uri.fsPath, '.env');
        const envContent = `${varName}=${secretValue}\n`;
        try {
            // 1. Create or Append to the .env file
            if (!fs.existsSync(envPath)) {
                fs.writeFileSync(envPath, envContent);
            }
            else {
                fs.appendFileSync(envPath, envContent);
            }
            // 2. Add .env to .gitignore so it never leaks
            const gitignorePath = path.join(workspaceFolders[0].uri.fsPath, '.gitignore');
            if (fs.existsSync(gitignorePath)) {
                const gitignore = fs.readFileSync(gitignorePath, 'utf8');
                if (!gitignore.includes('.env')) {
                    fs.appendFileSync(gitignorePath, '\n.env\n');
                }
            }
            else {
                fs.writeFileSync(gitignorePath, '.env\n');
            }
            vscode.window.showInformationMessage(`✅ Neural-Sentinel: '${varName}' securely moved to .env and hidden from Git.`);
        }
        catch (err) {
            vscode.window.showErrorMessage("Failed to update .env: " + err);
        }
    });
    // --- NEW: Virtual Document Provider for Side-by-Side Diff ---
    const previewProvider = new class {
        constructor() {
            this.content = "";
            this.onDidChangeEmitter = new vscode.EventEmitter();
            this.onDidChange = this.onDidChangeEmitter.event;
        }
        setContent(newContent) {
            this.content = newContent;
            // Notify VS Code that the virtual document has updated
            this.onDidChangeEmitter.fire(vscode.Uri.parse('sentinel-preview:Proposed-Fix'));
        }
        provideTextDocumentContent(uri) {
            return this.content;
        }
    };
    context.subscriptions.push(vscode.workspace.registerTextDocumentContentProvider('sentinel-preview', previewProvider));
    // --- NEW: Command to Open the Diff and Apply Fix ---
    let previewFixDisposable = vscode.commands.registerCommand('neural-sentinel.previewFix', async (documentUri, replacementCode, assignmentRange, envVarName, secretValue) => {
        const document = await vscode.workspace.openTextDocument(documentUri);
        const fullText = document.getText();
        // 1. Calculate what the file WOULD look like
        const startOffset = document.offsetAt(assignmentRange.start);
        const endOffset = document.offsetAt(assignmentRange.end);
        const proposedText = fullText.substring(0, startOffset) + replacementCode + fullText.substring(endOffset);
        // 2. Set the virtual document content
        previewProvider.setContent(proposedText);
        // 3. Open the Side-by-Side Diff Editor
        const previewUri = vscode.Uri.parse('sentinel-preview:Proposed-Fix');
        await vscode.commands.executeCommand('vscode.diff', documentUri, previewUri, `Neural-Sentinel: Original ↔ Secure (${envVarName})`);
        // 4. Ask the user to accept the remediation
        const choice = await vscode.window.showInformationMessage(`Accept this secure refactoring for ${envVarName}?`, "Accept Fix", "Decline");
        if (choice === "Accept Fix") {
            // Apply the actual code edit
            const edit = new vscode.WorkspaceEdit();
            edit.replace(documentUri, assignmentRange, replacementCode);
            await vscode.workspace.applyEdit(edit);
            // Trigger the .env extraction we built earlier
            vscode.commands.executeCommand('neural-sentinel.appendToEnv', envVarName, secretValue);
            // Close the diff window automatically
            vscode.commands.executeCommand('workbench.action.closeActiveEditor');
        }
    });
    // 4. Register the Code Action Provider (Multi-Language Support)
    const actionProvider = vscode.languages.registerCodeActionsProvider(['javascript', 'typescript', 'python', 'java', 'c', 'cpp'], // Expanded language support
    new NeuralSentinelFixer(), { providedCodeActionKinds: NeuralSentinelFixer.providedCodeActionKinds });
    // Register everything to the extension context (ADDED previewFixDisposable here)
    context.subscriptions.push(setupDisposable, scanDisposable, appendToEnvDisposable, previewFixDisposable, actionProvider);
}
// The logic that generates the Quick Fixes
class NeuralSentinelFixer {
    provideCodeActions(document, range, context) {
        const actions = [];
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.code && diagnostic.code.value === "extract-to-env") {
                const secretValue = diagnostic.code.target.toString();
                const variableName = document.getText(diagnostic.range);
                // Create the Fix Action
                const fix = new vscode.CodeAction(`Auto-Refactor '${variableName}' to .env`, vscode.CodeActionKind.QuickFix);
                // Determine the correct language syntax
                const langId = document.languageId;
                const envVarName = variableName.toUpperCase();
                let replacementCode = "";
                if (langId === 'python') {
                    replacementCode = `${variableName} = os.getenv("${envVarName}")`;
                }
                else if (langId === 'java') {
                    replacementCode = `String ${variableName} = System.getenv("${envVarName}");`;
                }
                else if (langId === 'c' || langId === 'cpp') {
                    replacementCode = `const char* ${variableName} = getenv("${envVarName}");`;
                }
                else {
                    // Default to JS/TS
                    replacementCode = `const ${variableName} = process.env.${envVarName};`;
                }
                // Expand range to cover the whole assignment
                const lineText = document.lineAt(diagnostic.range.start.line).text;
                const fullAssignmentRange = new vscode.Range(diagnostic.range.start.line, lineText.indexOf(variableName), diagnostic.range.start.line, lineText.length);
                // INSTEAD of applying the edit silently, trigger the Side-by-Side Diff Command
                fix.command = {
                    command: 'neural-sentinel.previewFix',
                    title: 'Preview Secure Refactor',
                    arguments: [
                        document.uri,
                        replacementCode,
                        fullAssignmentRange,
                        envVarName,
                        secretValue
                    ]
                };
                fix.diagnostics = [diagnostic];
                fix.isPreferred = true;
                actions.push(fix);
            }
        }
        return actions;
    }
}
exports.NeuralSentinelFixer = NeuralSentinelFixer;
NeuralSentinelFixer.providedCodeActionKinds = [vscode.CodeActionKind.QuickFix];
function deactivate() { }
//# sourceMappingURL=extension.js.map