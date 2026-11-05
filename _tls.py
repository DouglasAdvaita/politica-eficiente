import socket
import time

def probar(nombre, host, puerto):
    t = time.time()
    try:
        infos = socket.getaddrinfo(host, puerto, proto=socket.IPPROTO_TCP)
        dns = time.time() - t
        print(f"{nombre}: dns {dns:.2f}s -> {[i[4][0] for i in infos][:3]}", flush=True)
    except Exception as e:
        print(f"{nombre}: dns fallo {type(e).__name__} {e}", flush=True)
        return
    t = time.time()
    try:
        s = socket.create_connection((host, puerto), timeout=8)
        print(f"{nombre}: tcp ok en {time.time() - t:.2f}s", flush=True)
        s.close()
    except Exception as e:
        print(f"{nombre}: tcp fallo {type(e).__name__} {e}", flush=True)


probar("github", "api.github.com", 443)
probar("neon-pooler", "ep-purple-wave-b4d2g8io-pooler.c-6.us-east-2.aws.neon.tech", 5432)
