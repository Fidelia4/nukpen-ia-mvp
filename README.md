
# Nukpɛń_IA – Miroir intelligent de style

**Description :**
`Nukpɛń_IA` est un projet Python qui combine **intelligence artificielle** et interface **Streamlit** pour analyser les tenues vestimentaires. L’application permet de recevoir une analyse complète incluant : description, points forts, améliorations, accessoires, coiffure et maquillage, adaptée à une **occasion spécifique**.

Le projet utilise plusieurs modèles d’IA (OpenAI GPT-4.1-mini, Ollama Moondream / LLaVA, OpenRouter, Groq) pour générer des conseils vestimentaires détaillés.

---

## 1. Prérequis

* Python ≥ 3.11
* Git
* [Conda](https://www.anaconda.com/) ou `venv` pour créer un environnement isolé
* Clés API pour OpenAI / Ollama / autres (selon fournisseur choisi)

---

## 2. Installation de l’environnement Python

1. Créer un environnement conda :

```bash
conda create -n nukpen_ia python=3.11 -y
conda activate nukpen_ia
```

ou avec `venv` :

```bash
python -m venv nukpen_env
source nukpen_env/bin/activate  # Linux/Mac
nukpen_env\Scripts\activate     # Windows
```

2. Mettre à jour pip :

```bash
pip install --upgrade pip
```

---

## 3. Installation des dépendances Python

Toutes les librairies nécessaires sont dans `requirements.txt`. Exemple de commande :

```bash
pip install -r requirements.txt
```

**Si pas de fichier `requirements.txt`**, installer manuellement :

```bash
pip install streamlit pillow python-dotenv requests openai
```

* `streamlit` : interface web interactive
* `Pillow` : traitement d’images (redimensionnement, conversion)
* `python-dotenv` : gestion des fichiers `.env` pour les clés API
* `requests` : requêtes HTTP vers Ollama ou autre API
* `openai` : pour utiliser GPT-4.1-mini et autres modèles OpenAI

---

## 4. Configuration des clés API

Créer un fichier `.env` à la racine du projet :

```env
OPENAI_API_KEY="votre_cle_api_openai"
OPENROUTER_API_KEY="votre_cle_api_openrouter"
GROQ_API_KEY="votre_cle_api_groq"
```

> Assurez-vous que vos clés sont valides et ont suffisamment de crédits pour faire des requêtes.

---

## 5. Installation de Ollama (pour Windows)

Ollama est utilisé pour exécuter des modèles locaux comme `Moondream` et `LLaVA`.

1. Télécharger Ollama : [https://ollama.com/download](https://ollama.com/download)
2. Installer Ollama
3. Lancer le serveur local avant d’exécuter l’application :

```bash
ollama serve
```

4. Télécharger les modèles nécessaires :

```bash
ollama pull moondream
ollama pull llava:7b
```

---

## 6. Structure du projet

```
nukpen_ia_mvp/
├── app.py               # Fichier principal Streamlit
├── analysis.py          # Module d'analyse avec IA
├── prompt.py            # Fonctions pour générer les prompts pour les IA
├── requirements.txt
├── .env                 # Clés API
├── images/              # Logos et images miroirs
│   ├── logo.png
│   └── miroir.jpeg
├── style.css            # Styles CSS pour l’UI Streamlit
```

---

## 7. Lancer l’application

1. Activer l’environnement Python :

```bash
conda activate nukpen_ia
```

2. Lancer Streamlit :

```bash
streamlit run app.py
```

* Accès local : [http://localhost:8501](http://localhost:8501)
* Accès réseau : `http://<IP_LOCAL>:8501`

> Assurez-vous que le serveur Ollama est lancé si vous utilisez le modèle `Moondream`.

---

## 8. Utilisation de l’application

1. **Logo principal** : en haut de la page
2. **Chargement d’image miroir** : centré au milieu
3. **Analyse IA** : affichée dans les boîtes résultats
4. Les boutons Streamlit permettent de relancer l’analyse avec un autre modèle ou image.

---

## 9. IA et modèles utilisés

| Fournisseur | Modèle               | Usage                                         |
| ----------- | -------------------- | --------------------------------------------- |
| OpenAI      | GPT-4.1-mini         | Analyse principale, génération JSON           |
| Ollama      | Moondream / LLaVA    | Analyse locale, fallback si sortie incomplète |
| OpenRouter  | GPT-4o-mini          | Alternative OpenAI compatible entreprise      |
| Groq        | LLaMA 3.2 11B Vision | Analyse image + texte (optionnel)             |

**Remarques techniques :**

* Les modèles OpenAI requièrent une connexion Internet et clé API.
* Ollama fonctionne en local, utile pour éviter le quota OpenAI ou pour la confidentialité.
* Le module `analysis.py` gère : encodage image, prompt, extraction JSON et correction des sections manquantes.

---

## 10. Conseils et debug

* Si `NameError: _analyze_with_ollama` → vérifier que `analysis.py` contient bien la fonction `_analyze_with_ollama`.
* Si `ConnectionError` → assurez-vous que Ollama est lancé (`ollama serve`).
* Pour des réponses incomplètes → changer le modèle ou relancer l’analyse.
* Streamlit responsive → redimensionner le navigateur pour voir l’adaptabilité.
