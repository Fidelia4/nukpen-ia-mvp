def build_prompt(occasion):
    return f"""
Tu es un styliste expert en mode africaine et moderne.

Analyse la tenue sur l'image fournie.

Donne une réponse structurée :

1. Description de la tenue
2. Points forts
3. Améliorations recommandées
4. Accessoires conseillés
5. Coiffure adaptée
6. Maquillage conseillé

Adapte tes conseils pour cette occasion : {occasion}

Prends en compte l’élégance et l’harmonie culturelle.
"""
