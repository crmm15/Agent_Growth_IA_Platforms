# 🧠 Agent GrowthIA M&M – Plataforma GPT de Gestión Patrimonial

Esta aplicación combina inteligencia artificial, análisis cuantitativo y simulación de opciones para ayudarte a gestionar y proteger tu portafolio como lo haría un gestor profesional.

## 🚀 Funcionalidades integradas

- 📊 **Gestor de portafolio**  
  Revisa tus posiciones, evalúa rentabilidad y sugiere cobertura o mantenimiento.

- 📈 **Simulador de opciones con Delta**  
  Calcula prima, payoff y probabilidad implícita de éxito según tu perfil de riesgo (CALL o PUT).

- 📉 **Dashboard de desempeño histórico**  
  Analiza decisiones pasadas con visualizaciones de rentabilidad por ticker y acción tomada.

## ⚙️ Archivos clave

- `plataforma_gpt_inversiones.py`: archivo principal de la app (corre en Streamlit)
- `requirements.txt`: dependencias para correr en la nube
- `registro_acciones.csv`: log de decisiones tomadas (se genera automáticamente)

## ▶️ ¿Cómo correrlo?

### Localmente
```bash
pip install -r requirements.txt
streamlit run plataforma_gpt_inversiones.py
