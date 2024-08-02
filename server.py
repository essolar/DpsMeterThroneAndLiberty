import asyncio
import websockets
import json

connected_clients = {}

async def handle_client(websocket, path):
    # Registrar el cliente
    try:
        # Recibir el primer mensaje con el nombre del cliente
        initial_message = await websocket.recv()
        data = json.loads(initial_message)
        client_name = data['name']
        connected_clients[client_name] = websocket
        print(f"Client connected: {client_name}")

        async for message in websocket:
            data = json.loads(message)
            print(f"Received data from {client_name}: {data}")
            # Enviar la información a todos los clientes conectados
            for client in connected_clients:
                if client != client_name:
                    await connected_clients[client].send(json.dumps({client_name: data}))

    except websockets.ConnectionClosed:
        print(f"Client disconnected: {client_name}")
    finally:
        # Desregistrar el cliente
        del connected_clients[client_name]

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("Server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
