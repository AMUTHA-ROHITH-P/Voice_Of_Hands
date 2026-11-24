# 🤟 Voice of Hands (ISL Studio)

**A browser-based Indian Sign Language (ISL) communication tool that recognizes hand signs through your camera and turns them into text, so signers and hearing people can talk to each other.**

> Final year project by **Amutha Rohith P**

<!-- Add a demo GIF or screenshots here, e.g.
![Demo](docs/demo.gif)
-->

---

## ✨ Features

- **Live sign recognition** from the browser camera (no installs on the user's side)
  - **Letter and word signs:** static hand shapes matched against saved templates
  - **Motion signs:** signs that involve movement, matched using Dynamic Time Warping (DTW)
- **Two-way conversation board:** a large text pane for the signer and a typed-reply pane for the hearing person
- **Quick-phrase tiles and next-word suggestions** to speed up sentences
- **Translation into about 13 languages** with automatic fallbacks (local NLLB model, Google Cloud Translation, MyMemory, free Google Translate)
- **Train your own signs:** administrators can record new letter, word and motion signs from the app
- **Sign dictionary** with flashcards, plus a transcript showing each recognized sign with its confidence
- **Accessibility first:** every cue is visual (no audio needed), with dark and light themes, font scaling, reduced motion, high-contrast captions and screen-flash confirmations
- **User accounts and roles:** User and Administrator, with PBKDF2-SHA256 salted password hashing

---

## 🧠 How It Works

1. **Hand detection:** MediaPipe Hands extracts 21 hand landmarks from each camera frame.
2. **Static signs (letters and words):** Landmarks are normalized (wrist-centred and scaled) and compared with each sign's template using cosine similarity. Low-confidence matches are discarded.
3. **Motion signs:** Hand movement is automatically segmented, resampled to a fixed length, and matched with banded DTW. Each sign's tolerance is calibrated from its training samples.
4. **Output:** Recognized signs are added to the conversation board, and can be translated into the selected language.

---

## 🛠️ Tech Stack

| Area | Technology |
|---|---|
| UI | Streamlit, streamlit-webrtc |
| Hand tracking | MediaPipe |
| Image overlays | OpenCV |
| Matching | NumPy (cosine similarity, custom DTW) |
| Database | SQLite (`voiceofhands.db`) via `db.py` |
| Translation (optional) | deep_translator, requests, transformers/torch (offline NLLB-200) |
| Language | Python |

---

## 📁 Project Structure

```
Voice_Of_Hands/
├── app.py                    # Main Streamlit app (UI, auth, recognition, translation)
├── db.py                     # Database layer (users, signs, motion samples, metadata)
├── seed.py                   # Seeds the database with initial data
├── migrate_json_to_db.py     # Migrates old JSON data into SQLite
├── check_db.py / view_database.py   # Helper scripts to inspect the database
├── requirements.txt          # Python dependencies
├── packages.txt              # System packages (for deployment)
├── voiceofhands_data/        # Data folder
└── .devcontainer/            # Dev container configuration
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or newer
- A webcam and a modern browser (Chrome or Edge recommended)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AMUTHA-ROHITH-P/Voice_Of_Hands.git
cd Voice_Of_Hands

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) seed the database
python seed.py

# 5. Run the app
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501) and allow camera access.

### Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `VOH_ADMIN_CODE` | Code required to create an Administrator account. **Set your own value.** |
| `VOH_LOCAL_MT=1` | Use the offline NLLB-200 translation model (needs `transformers` and `torch`) |

---

## 📖 Usage

1. **Create an account** (User or Administrator) and log in.
2. **Allow camera access** and start the recognizer.
3. **Sign in front of the camera.** Recognized letters and words appear on the conversation board.
4. **Reply by typing** in the hearing-side pane, and use quick phrases or suggestions to go faster.
5. **Translate** the conversation into your preferred language.
6. **Admins:** open the training section to record new letter, word or motion signs.

---

## ⚠️ Limitations

- Recognition accuracy depends on lighting, camera quality and hand visibility.
- The sign vocabulary is limited to the signs that have been trained.
- Online translation needs an internet connection (offline mode needs extra setup).

## 🔮 Future Work

- Expand the ISL vocabulary and add sentence-level recognition
- Add text-to-sign output (avatar or video) for two-way communication
- Mobile-friendly or app version
- Larger multi-user dataset to improve accuracy

---

## 🤝 Contributing

Suggestions and contributions are welcome. Open an issue or submit a pull request.

## 📄 License

Add a license of your choice, for example MIT, by creating a `LICENSE` file.

## 👤 Author

**Amutha Rohith P**
GitHub: [@AMUTHA-ROHITH-P](https://github.com/AMUTHA-ROHITH-P)
