# WhisperSpeech

[![Test it out yourself in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1xxGlTbwBmaY6GKA24strRixTXGBOlyiw)
[![](https://dcbadge.vercel.app/api/server/FANw4rHD5E)](https://discord.gg/FANw4rHD5E)  
*Join us in the **#audio-generation** channel on the LAION Discord to chat, ask questions, or contribute!*

**WhisperSpeech** is an open-source, text-to-speech (TTS) system created by “inverting” OpenAI Whisper.  
Our goal is to be for speech what Stable Diffusion is for images—powerful, hackable, and commercially safe.

* All code is Apache-2.0 / MIT.  
* Models are trained only on properly licensed data.  
* Current release: English (LibreLight). Multilingual release coming next.

**Sample output →**

https://github.com/collabora/WhisperSpeech/assets/107984/aa5a1e7e-dc94-481f-8863-b022c7fd7434

## 🚀 Progress Updates

<details><summary><strong>[2024-01-29]</strong> – Tiny S2A multilingual voice-cloning</summary>

We trained a **tiny** S2A model on an **en + pl + fr** dataset; it successfully clones French voices using semantic tokens frozen on English + Polish—evidence that one tokeniser could cover *all* languages.

https://github.com/collabora/WhisperSpeech/assets/107984/267f2602-7eec-4646-a43b-059ff91b574e  
https://github.com/collabora/WhisperSpeech/assets/107984/fbf08e8e-0f9a-4b0d-ab5e-747ffba2ccb9
</details>

<details><summary><strong>[2024-01-18]</strong> – 12× real-time on a 4090 + voice-cloning demo</summary>

* Added `torch.compile`, KV-caching, and layer tweaks → **12× faster-than-real-time** on a consumer RTX 4090.  
* Seamlessly code-switch within one sentence:

> To jest pierwszy test wielojęzycznego `Whisper Speech` modelu …  

https://github.com/collabora/WhisperSpeech/assets/107984/d7092ef1-9df7-40e3-a07e-fdc7a090ae9e

* One-click voice-cloning—example based on Winston Churchill’s [“Be Ye Men of Valour”](https://en.wikipedia.org/wiki/File:Winston_Churchill_-_Be_Ye_Men_of_Valour.ogg) (radio static preserved by design):

https://github.com/collabora/WhisperSpeech/assets/107984/bd28110b-31fb-4d61-83f6-c997f560bc26

[Test it on Colab](https://colab.research.google.com/drive/1xxGlTbwBmaY6GKA24strRixTXGBOlyiw) (≤ 30 s install). Hugging Face Space coming soon.
</details>

<details><summary><strong>[2024-01-10]</strong> – Faster SD S2A + first cloning example</summary>

A new SD‑size S2A model brings major speed‑ups without sacrificing quality; cloning example added.  
[Try it on Colab](https://colab.research.google.com/drive/1xxGlTbwBmaY6GKA24strRixTXGBOlyiw).
</details>

<details><summary><strong>[2023-12-10]</strong> – Multilingual trio (EN/PL)</summary>

* English (female voice transferred from a Polish dataset):  
  https://github.com/collabora/WhisperSpeech/assets/107984/aa5a1e7e-dc94-481f-8863-b022c7fd7434  
* Polish (male voice):  
  https://github.com/collabora/WhisperSpeech/assets/107984/4da14b03-33f9-4e2d-be42-f0fcf1d4a6ec  

[Archive of older updates](https://github.com/collabora/WhisperSpeech/issues/23)
</details>

## 📊 Community Benchmarks

Unofficial speed & memory‑usage results from the community can be found [here](https://github.com/WhisperSpeech/WhisperSpeech/issues/131).

## 📦 Downloads

* **Quick start:** open the Colab above or run the notebook locally.  
* **Manual:**  
  * Pre‑trained models – <https://huggingface.co/collabora/whisperspeech>  
  * Converted datasets – <https://huggingface.co/datasets/collabora/whisperspeech>

## 🗺️ Roadmap

- [ ] [Gather large emotive‑speech dataset](https://github.com/collabora/spear-tts-pytorch/issues/11)  
- [ ] Condition generation on emotion & prosody  
- [ ] Community drive for freely licensed multilingual speech  
- [ ] [Train final multilingual models](https://github.com/collabora/spear-tts-pytorch/issues/12)

## ⚙️ Architecture

WhisperSpeech follows the two‑stage, token‑based pipeline popularised by  
[AudioLM](https://google-research.github.io/seanet/audiolm/examples/), Google’s [SPEAR TTS](https://google-research.github.io/seanet/speartts/examples/), and Meta’s [MusicGen](https://ai.honu.io/papers/musicgen/):

| Stage | Model | Purpose |
|-------|-------|---------|
| **Semantic** | [**Whisper**](https://github.com/openai/whisper) | Transcription ➜ semantic tokens |
| **Acoustic** | [**EnCodec**](https://github.com/facebookresearch/encodec) | Tokenise waveform (1.5 kbps) |
| **Vocoder** | [**Vocos**](https://github.com/charactr-platform/vocos) | High‑fidelity audio |

<details><summary>EnCodec architecture diagram</summary>

![EnCodec block diagram](https://github.com/facebookresearch/encodec/raw/main/architecture.png)

</details>

<details><summary>Conference talks (deep dives)</summary>

[![](https://img.youtube.com/vi/6Fr-rq-yjXo/0.jpg)](https://www.youtube.com/watch?v=6Fr-rq-yjXo)  
*Tricks Learned from Scaling WhisperSpeech Models to 80k+ Hours of Speech* – Jakub Cłapa, Collabora  

[![](https://img.youtube.com/vi/1OBvf33S77Y/0.jpg)](https://www.youtube.com/watch?v=1OBvf33S77Y)  
*Open‑Source TTS Projects: WhisperSpeech – In‑Depth Discussion*
</details>

## 🙏 Appreciation

[<img height=80 src="https://user-images.githubusercontent.com/107984/229537027-a6d7462b-0c9c-4fd4-b69e-58e98c3ee63f.png" alt="Collabora logo">](https://www.collabora.com)      [<img height=80 src="https://user-images.githubusercontent.com/107984/229535036-c741d775-4a9b-4193-89a0-9ddb89ecd011.png" alt="LAION logo">](https://laion.ai)

Made possible by:

* **[Collabora](https://www.collabora.com)** – code & training  
* **[LAION](https://laion.ai)** – community & datasets  
* **[Jülich Supercomputing Centre](https://www.fz-juelich.de/en)** – JUWELS Booster  

Additional compute funded by the Gauss Centre for Supercomputing via the John von Neumann Institute for Computing (NIC).

Special thanks to individual contributors:  
* [@inevitable-2031](https://github.com/inevitable-2031) (`qwerty_qwer` on Discord) for dataset curation

## 💼 Consulting

Need help with open‑source or proprietary AI projects?  
Contact us via [Collabora](https://www.collabora.com) or DM on Discord:  
[![](https://dcbadge.vercel.app/api/shield/270267134960074762?style=flat)](https://discordapp.com/users/270267134960074762) 
[![](https://dcbadge.vercel.app/api/shield/1088938086400016475?style=flat)](https://discordapp.com/users/1088938086400016475)

---

## 📚 Citations

```bibtex
@article{SpearTTS,
  title       = {Speak, Read and Prompt: High-Fidelity Text-to-Speech with Minimal Supervision},
  url         = {https://arxiv.org/abs/2302.03540},
  author      = {Kharitonov, Eugene and Vincent, Damien and Borsos, Zalán and Marinier, Raphaël and Girgin, Sertan and Pietquin, Olivier and Sharifi, Matt and Tagliasacchi, Marco and Zeghidour, Neil},
  publisher   = {arXiv},
  year        = {2023},
}
```

```bibtex
@article{MusicGen,
  title     = {Simple and Controllable Music Generation},
  url       = {https://arxiv.org/abs/2306.05284},
  author    = {Jade Copet and Felix Kreuk and Itai Gat and Tal Remez and David Kant and Gabriel Synnaeve and Yossi Adi and Alexandre Défossez},
  publisher = {arXiv},
  year      = {2023},
}
```

```bibtex
@article{Whisper,
  title     = {Robust Speech Recognition via Large-Scale Weak Supervision},
  url       = {https://arxiv.org/abs/2212.04356},
  author    = {Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  publisher = {arXiv},
  year      = {2022},
}
```

```bibtex
@article{EnCodec,
  title     = {High Fidelity Neural Audio Compression},
  url       = {https://arxiv.org/abs/2210.13438},
  author    = {Défossez, Alexandre and Copet, Jade and Synnaeve, Gabriel and Adi, Yossi},
  publisher = {arXiv},
  year      = {2022},
}
```

```bibtex
@article{Vocos,
  title     = {Vocos: Closing the Gap Between Time‑Domain and Fourier‑Based Neural Vocoders for High‑Quality Audio Synthesis},
  url       = {https://arxiv.org/abs/2306.00814},
  author    = {Hubert Siuzdak},
  publisher = {arXiv},
  year      = {2023},
}
```
