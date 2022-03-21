// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
//const { once } = require('events');
const vscode = require('vscode');
const net = require('net');

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "emotionawareide" is now active!');

	// The command has been defined in the package.json file
	let disposable = vscode.commands.registerCommand('emotionawareide.start_dashboard', () => {

		// creates a webview
		const panel = vscode.window.createWebviewPanel(
			"dashboard",
			"Dashboard",
			vscode.ViewColumn.One,
			{
				enableScripts: true
			}
		);

		// gets the html to display
		panel.webview.html = getWebviewContent();
	});

	// pushes command to context
	context.subscriptions.push(disposable);

	// pushes command to context
	context.subscriptions.push(vscode.commands.registerCommand('emotionawareide.show_message', async () => {

		// gets message from user input
		let message = await vscode.window.showInputBox({
			placeHolder: "Write a message"
		});

		// runs displaymessage with message
		displayMessage(message);
		client.write(message);
	}));



	// port used for communication
	const port1 = 1337;

	// initialize client
	var client = new net.Socket();

	// connect client
	client.connect(port1, '127.0.0.1', () => {
		console.log('Connected');
		if (client) {
			client.write('Hello, server! Love, Client.');
		}
	});

	// on data received run function
	client.on('data', (data) => {

		// if nulls disconnect
		if (data == "\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"){
			console.log("Disconnecting client.")
			client.destroy();

		// write message
		} else {
			displayMessage('Received: ' + data);
		}
	});
}


function displayMessage(message) {
	// displays message as popup
	vscode.window.showInformationMessage(message);
}


function getWebviewContent() {
	// returns html as a iframe
	return `<!DOCTYPE html>
	<html>
	  
	<head>
		<title>full screen iframe</title>
		<style type="text/css">
			html {
				overflow: auto;
			}
			  
			html,
			body,
			div,
			iframe {
				margin: 0px;
				padding: 0px;
				height: 100%;
				border: none;
			}
			  
			iframe {
				display: block;
				width: 100%;
				border: none;
				overflow-y: auto;
				overflow-x: hidden;
			}
		</style>
	</head>
	  
	<body>
		<iframe src="http://localhost:8050"
				frameborder="0" 
				marginheight="0" 
				marginwidth="0" 
				width="100%" 
				height="100%" 
				scrolling="auto">
	  </iframe>
	  
	</body>
	  
	</html>`;
}


// this method is called when your extension is deactivated
function deactivate() {}

module.exports = {
	activate,
	deactivate
}
