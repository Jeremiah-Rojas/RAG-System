# RAG System

<img width="1846" height="887" alt="rag-system" src="https://github.com/user-attachments/assets/7c59149e-d6bd-4d65-b4e7-2c62af6dfe41" />

This workflow is meant to roughly simulate a log risk analysis and the actions that should be taken.
</br>This workflow automatically pulls logs from Splunk, a SIEM platform, and uses Google Gemini which gives a “risk score” assessing how serious an action must be taken, if any, according to what the security logs show. If the score is low, it simply archives the analysis. If the risk score is slightly concerning, an entry is made in Google Sheets as a form of ticketing for security personnel to address when they can. And if the risk score is high, and email is sent using Gmail directly to the Security personnel. This is all done automatically with no human interaction; it simply takes the click of a button.

</br>Below is each node explained in a little more detail about what is happening.

### Devices Used:
- Claude AI
- Python
- HTML
- OpenAI API (Brain of system)

## Node Details
