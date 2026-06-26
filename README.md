# RAG System

<img width="1846" height="887" alt="rag-system" src="https://github.com/user-attachments/assets/7c59149e-d6bd-4d65-b4e7-2c62af6dfe41" />

The image above shows the RAG system in action. A RAG (Retrieval-Augmented Generation) System is an AI powered system that uses the data/documents given to it for context on how to respond accurately. You can drag and drop files you want uploaded and they will be shown to the left.


</br>The first thing you must do for the system to work properly is enter your OpenAI API key; note that this system will not work with any other LLM. After that, it’s as simple as uploading documents and asking questions based on those documents. Note, it’s best to specify what document you want it to search by calling it by its full file name.
</br>


This is the prompt I gave Claude to build out this system; this was done with a free Claude account. The more descriptive you are, the better it will build the system according to how you imagine it:
```
Build a RAG system with a Web interface with a dark futuristic look consisting of dark gray, black, blue, and white.
This RAG system will be accessible only to me on my local computer and should have a place for me to enter text according to what I want it to do.
Follow these specifications:
Input: The input will be text entered in by the user so there should be a space to type in the prompt. There should also be a place where I can upload files on my local computer to the RAG system so that it can have context on how to answer the prompts.
AI brain: This RAG system will use the OpenAI LLM so make it clear where I need to enter in my OpenAI API key.
Task: This RAG system will always answer any questions asked only according to the documents given to it; in this case the files uploaded by me. If possible, before and after every prompt message and response, show how many API credits/tokens I have remaining.
Output: This system will answer the user prompts using only the files given to it. The answers will be succinct.
Example usage:
Prompt: According to the PSCI 432 document, how should I perform legal analysis?
Response: (looking through PSCI 432 document). You perform legal analysis by following these steps: …etc.
Make it clear what I need to do to start using this tool and how to properly terminate it.
If files needed to be created and stored locally on my computer for this program to work, make this clear and show me which files require this.
```
</br>After running this prompt, Claude created all the files necessary for this program to run and even inlcuded instructions on how to set it up. These are shown [here](https://github.com/Jeremiah-Rojas/RAG-System/blob/main/rag_system/README.md)
</br>
The image below shows what the “TEST.txt” document contains, which is just the secret along with filler text:
</br>
<img width="1006" height="482" alt="image" src="https://github.com/user-attachments/assets/9c19ba90-dbcd-4b66-bd2a-ffa4d6afb349" />

</br>
Although you can upload PDF, DOCX, and MD files as well as text documents, I chose to upload a .txt file for simplicity sake.

## Startup

See the instructions in [this file](https://github.com/Jeremiah-Rojas/RAG-System/blob/main/rag_system/README.md) on how to properly set up this system. Note that when downloading these files, the file structure must remain identical to how it is set up here in github:
```
—rag_system
          |___README.md
          |___app.py
          |___requirements.txt
          |___static
		 |___index.html
```      
</br>If the file/folder structure is changed, even the names, the system will throw an error.


</br>Below is the system starting up:
</br><img width="1362" height="662" alt="rag-startup" src="https://github.com/user-attachments/assets/59a6f6a0-1d27-45f2-9b42-def85bda667f" />


## Persistence

After uploading files and then closing it down, a certain file and folder are created in order to maintain any documents you uploaded in previous sessions. Also, the API Key you enter is not saved anywhere but instead resides in memory and disappears every time you close the system so every time you wish to use the system, you must re-enter the same API Key every time; you do not need to create a new API Key every time.


</br>Below is the file and folder created (rag_index.pkl, uploads) when starting a new session:
</br><img width="1050" height="307" alt="rag-persistence" src="https://github.com/user-attachments/assets/845b8a42-7344-4327-abda-249a1bffa450" />

## Conclusion

This project is not about replacing people but showing the capabilities of AI and how to more effectively conduct certain tasks which previously would've have taken days if not weeks; with Claude, this project was setup in a matter of minutes. To anyone who may come across this, I hope you find this useful.

### Devices Used:
- Claude AI
- Python
- HTML
- OpenAI API (Brain of system)
