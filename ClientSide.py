import asyncio
import websockets
import json

async def send_data(websocket, name, data):
    message = json.dumps({'name': name, 'data': data})
    await websocket.send(message)

async def receive_data(websocket, on_message_callback):
    async for message in websocket:
        data = json.loads(message)
        on_message_callback(data)

async def start_websocket(name, on_message_callback, host_ip):
    uri = f'ws://{host_ip}:8765'
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({'name': name}))
        await receive_data(websocket, on_message_callback)

async def send_dps_data(websocket, name, dps, total_damage, elapsed_time):
    data = {
        'dps': dps,
        'total_damage': total_damage,
        'elapsed_time': elapsed_time
    }
    await send_data(websocket, name, data)
