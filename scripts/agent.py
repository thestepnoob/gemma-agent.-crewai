import sys

# Standardausgabe und Standardfehler auf UTF-8 umstellen, um Windows-Encoding-Fehler bei Unicode-Zeichen zu vermeiden
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Custom CrewAI Tool wrapper for LangChain's DuckDuckGoSearchRun
class DuckDuckGoSearchTool(BaseTool):
    name: str = "DuckDuckGo Search Tool"
    description: str = "Search the web for a given query."
    
    def _run(self, query: str) -> str:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)

# 2. Lokale Gemma 4 über Ollama mit dem neuen CrewAI LLM-Objekt einbinden
llm = LLM(
    model="ollama/gemma4:12b",
    base_url="http://localhost:11434",
    temperature=0.3
)

# 3. Werkzeug instanziieren
search_tool = DuckDuckGoSearchTool()

# 4. Den autonomen Agenten definieren
projekt_manager = Agent(
    role='Autonomer Projektmanagement-Experte',
    goal='Analysiere, übersetze und strukturiere komplexe Fachdokumente selbstständig.',
    backstory='Du bist ein präziser, analytischer Agent. Du triffst Entscheidungen autonom, korrigierst deine Fehler selbst und nutzt Tools, um Fakten zu prüfen.',
    verbose=True, # Zeigt dir im Terminal live, was der Agent gerade "denkt" und tut
    allow_delegation=False,
    llm=llm,
    tools=[search_tool]
)

# 5. Die konkrete Aufgabe festlegen
aufgabe = Task(
    description='''
    Untersuche die Ordnerstruktur und die Fachbegriffe aus dem Projektmanagement Kurs.
    Falls du auf unklare vietnamesische Begriffe stößt, nutze das Suchwerkzeug, um die korrekte agile englische oder deutsche Entsprechung zu finden.
    Erstelle eine saubere, deutsche Zusammenfassung der Kernkonzepte.
    ''',
    expected_output='Eine perfekt strukturierte Dokumentation im Markdown-Format.',
    agent=projekt_manager
)

# 6. Den Agenten in die Autonomie-Schleife starten
crew = Crew(
    agents=[projekt_manager],
    tasks=[aufgabe],
    process=Process.sequential
)

print("--- Agent startet die autonome Arbeit ---")
ergebnis = crew.kickoff()
print("--- Aufgabe beendet ---")
print(ergebnis)
