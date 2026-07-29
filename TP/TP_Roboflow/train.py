from ultralytics import YOLO
import os

# Sécurité pour éviter que les paquets de données du GPU se rentrent dedans
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

if __name__ == '__main__':
    model = YOLO(r'#chemin exact de votre best.pt')

    # 2. Lancer l'entraînement avec les correctifs anti-biais et anti-overfitting
    model.train(
        data=r'chemin exact de votre data.yaml',
        epochs=40,         
        imgsz=640,
        batch=8,             
        workers=0,
        amp=False,           
        
        # --- CORRECTIFS POUR MULTIPLIER LES PANNEAUX ET EFFACER LE FOND ---
        mosaic=1.0,          # Forcé à 1.0 pour mélanger les contextes au maximum
        mixup=0.2,           # Superpose deux images pour détruire la mémoire du décor de la salle
        scale=0.6,           # Zoom / Dézoom de +/- 60% pour détacher les panneaux du fond arrière
        hsv_h=0.015,         # Perturbe légèrement les teintes pour que le modèle ne se fie pas aux couleurs de la pièce
        
        # --- FORCE LA CLASSIFICATION DES CLASSES ---
        cls=3.0,             # Multiplie par 6 l'importance de la classification (0.5 par défaut) pour corriger le bug des feux partout
        
        save=True,           
        save_period=1,       # Sauvegarde à chaque époque pour pouvoir piocher l'époque qu'on veut si surentrainé par exemple
        
        name='#nom que vous souhaitez', 
        project=r'#chemin de la sauvegarde'
    )
    print("Entraînement terminé !")
