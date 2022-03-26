const net = require('net');


// import { WebSocket } from "ws";

function main (){
    if (process.argv.length == 3)
    {
        let port = 0;
        try {
            port = parseInt(process.argv[2]);
            console.log(port);
        } catch(error) {
            //console.error(error)
        }
        return port
    }
    return 0
}

// const socket = new WebSocket("ws://localhost:8085")

// socket.on('message', (data) => {
//     console.log(data);
// });

function byteToFloat(data) {
    // Create a buffer
    let buf = new ArrayBuffer(4);
    // Create a data view of it
    let view = new DataView(buf);

    // set bytes
    data.forEach(function (b, i) {
       view.setUint8(i, b);
    });

    // Read the bits as a float; note that by doing this, we're implicitly
    // converting it from a 32-bit float into JavaScript's native 64-bit double
    let num = view.getFloat32(0, true);
    return num;
}

let END_MSG = "\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"

class StreamMessage{
    constructor(message){
        this.OG_message = message;
        this.send_msg = message + "\t\n";
    }
    get sendable() {
        return this.send_msg;
    }
}

const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
});

function convert_message(data) {
    console.log("FPOGX: " + byteToFloat(data.slice(0,4)));
    console.log("FPOGY: " + byteToFloat(data.slice(4,8)));
    let arousal = "LOW";
    if (data[8] == 1)
    {
        arousal = "HIGH";
    }
    console.log("Arousal: " + arousal + ", Certanty: " + byteToFloat(data.slice(9,13)));
    
    let valence = "LOW";
    if (data[13] == 1)
    {
        valence = "HIGH";
    }
    console.log("Valence: " + valence + ", Certanty: " + byteToFloat(data.slice(14, 18)));
}

port1 = main();
if (port1) {

    var client = new net.Socket();
    client.connect(port1, '127.0.0.1', function() {
        console.log('Connected');
        client.write("FRM Tjabba\t\n")
    });

    client.on('data', function(data) {
        if (data == END_MSG){
            console.log("Disconnecting client.")
            client.destroy();
        } else {
            console.log(data.toString())
        }
    });
    
    // let input_message = "";
    // readline.question("Input: ", input =>{
    //     input_message = input + "\t\n";
    //     if(input == "!Q")
    //     {
    //         readline.close();
    //         client.write("END SERVER");
    //     }
    //     else
    //         client.write(input_message);
    // });
}

