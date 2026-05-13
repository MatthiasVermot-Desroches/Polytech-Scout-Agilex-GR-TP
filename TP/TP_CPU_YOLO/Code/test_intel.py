import openvino as ov

core = ov.Core()
devices = core.available_devices

print("--- Rapport de ton Protocole ---")
for device in devices:
    full_name = core.get_property(device, "FULL_DEVICE_NAME")
    print(f"Matériel détecté : {device} ({full_name})")

if 'GPU' in devices:
    print("\nSUCCÈS : Ton GPU Intel Arc est prêt pour YOLOv11 !")
else:
    print("\nATTENTION : Seul le CPU est visible. Vérifie tes accès Docker.")
