# emotionawareide README

## How do I add a new command in the command palette?
To add a new command to the command palette you have to add it's entry in the file **package.json** in the **commands** section the entry is structured like
```json
{
    "command": "command to run goes here",
    "title": "The name displayed in the command palette goes here"
}
```

To supply the command that the is run we must specify in the **extenstion.js** file
```js
context.subscriptions.push(vscode.commands.registerCommand("same name supplied as the command in the json file goes here", "The function to goes here"));
```