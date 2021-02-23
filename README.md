**Chatidea**

Chatidea è un framework che permette di generare chatbot partendo dallo schema di una base di dati. 

**Requisiti ed esecuzione chatbot**

- [Python 3.7.6](https://www.python.org/downloads/release/python-376/ "Python 3.7.6")
- [Node.js](https://nodejs.org/it/ "Node.js")
- Installare chatito mediante il comando: ***npm i chatito –save***
- Installare il gestore delle dipendenze PIP: se non si ha nessuna versione di pip installata bisogna prima scaricare il file [get-pip.py](https://bootstrap.pypa.io/get-pip.py "get-pip.py") e lanciare il seguente comando dalla cartella dove avete scaricato il file: 
  ***python get-pip.py***
- Gestore delle dipendenze e ambienti virtuali installabile con comando 
  ***py -3.7 -m pip install pipenv*** (in ambiente UNIX il comando ***py*** viene sostituito dal comando ***python3**;* se su windows non dovesse funzionare il comando ***py*** provare con ***python***)
- Per installare tutte le dipendenze necessarie è sufficiente posizionarsi nella cartella Chatidea e lanciare i seguenti comandi in sequenza: 
  ***SET PIPENV\_VENV\_IN\_PROJECT=1 
  pipenv install*** 
- Prima di lanciare il chatbot ricordare di avere sul proprio sistema attivo MySql e di aver installato il database di riferimento del chatbot (**deib** nel caso corrente il cui dump è disponibile nella cartella *Chatidea\resources\db*). Seguire gli step della configurazione per collegare il chatbot al database 
- Per lanciare la chatbot dalla cartella Chatidea eseguire il comando 
  ***pipenv run python run.py***
- Dal browser ora il chabot è raggiungibile all’indirizzo ***localhost:5080***

**NB:** In Windows potrebbero verificarsi problemi nell’installazione della dipendenza ujson. Per risolvere tale problema bisogna installare gli strumenti per VC++ del sistema operativo. Per fare questo, scaricare [*Microsoft Build Tools 2015](https://visualstudio.microsoft.com/it/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16)*
Far partire l'installazione, al termine spuntare la casella "Strumenti di compilazione C++" e selezionare i seguenti strumenti:

![](Aspose.Words.f23d8044-f5b5-4422-83f7-d7efd661b613.001.png)

Dopo aver selezionato tutti questi componenti procedere con l’installazione. A installazione terminata, tornare nel prompt dei comandi e lanciare:

1. SET PIPENV\_VENV\_IN\_PROJECT=1 
1. pipenv install  

**Configurazione**

Le variabili di configurazione sono all'interno di ***Chatidea/settings.py***

-----
select = 'deib'

select\_dict = {

`    `'teachers': ['b', 'teachers', '797397572:AAEV1MfR28lTzPsom\_2qO2-goJSCKzQZ5d0'],

`    `'classicmodels': ['c', 'classicmodels', '710759393:AAGcrq2gkBd84qa-apwS9quMd5QK0knfWTM'],

`    `'deib': ['d', 'deib', '1046778538:AAF2CKzjxwzCu9fiDLgadBujYKuBKhgKmdE']

}

***select\_dict*** contiene una lista di database, è composto da: un carattere identificativo, il nome dello schema, l'API Key del bot telegram. ***select*** contiene il nome del database attualmente in uso.

-----
remote = True if os.environ.get('PYTHONANYWHERE\_SITE') else False

DATABASE\_USER = 'nicolacastaldo' if remote else 'root'

DATABASE\_PASSWORD = 'dataexplorerbot' if remote else ''

DATABASE\_HOST = 'nicolacastaldo.mysql.pythonanywhere-services.com' if remote else 'localhost'

DATABASE\_NAME = 'nicolacastaldo$classicmodels' if remote else db\_name

Cambiare user e password locali con i propri dati e, nel caso si voglia utilizzare un host remoto, modificare opportunamente la variabile d'ambiente e i dati restanti.

**Configurazione Webchat**

In caso di utilizzo di **https** usare la parte di codice commentata e inserire certificato e private key in ***Chatidea/modules/connectors***.

#sio = socketio.AsyncServer(cors\_allowed\_origins=[]) #Only for SSL workaround so that socketio works with requests from other origins.

sio = socketio.AsyncServer()

def start():

`    `#cert\_path = os.path.dirname(os.path.realpath(\_\_file\_\_))

`    `#context = ssl.create\_default\_context(purpose=ssl.Purpose.CLIENT\_AUTH)

`    `#context.load\_cert\_chain(certfile=cert\_path+ "/certificate.crt", keyfile= cert\_path+"/private.key")

`    `#web.run\_app(app, port=5080,ssl\_context=context)

`    `web.run\_app(app, port=5080)

Ricordare di cambiare il **socketUrl** dentro ***Chatidea/modules/connectors/index.html*** inserendo http o https e la porta giusta.

-----
La libreria utilizzata per gestire la webchat non sembra più raggiungibile. In alternativa potete usare:

<script src="https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.min.js"></script>

Al posto di:

<script src="https://storage.googleapis.com/mrbot-cdn/webchat-0.5.3.js"></script>

è necessario però modificare le personalizzazioni effettuate precedentemente in **index.html** adattandole alla nuova libreria.

**Come far partire il chatbot**

Dentro **Chatidea/run.py** decommentare in base all'ambiente in cui si vuole eseguire il chatbot.

`    `webchat.start()

`    `#telegram.start()

`    `#console\_input()

In **locale** posizionatevi dentro ***Chatidea*** e eseguite il comando python run.py

Per farlo partire su server Linux come servizio in background utilizzare **tmux** per non far terminare l'esecuzione dello script a sessione finita tmux new -s <nome-sessione> python run.py

Per riprendere il controllo della console dopo che si è usciti: tmux attach -t <nome-sessione>

**Fasi per la generazione di un chatbot**

Il processo di creazione di un nuovo chatbot può essere visto come una procedura semi-automatica, essendo costituita da azioni automatiche e manuali. Le azioni manuali sono quelle che dovranno essere svolte dal progettista e sono quelle che interessano l’annotazione dei dati.

**Database schema**

Creare un file JSON chiamato db\_schema\_<carattere\_identificativo>.json all'interno di ***Chatidea/resources/db***. Il file contiene una descrizione semplificata del database, evidenziandone la struttura in termini di attributi e relazioni.

Esempio di come descrivere una tabella:

`        `"location\_locali": {

`                `"column\_list": [

`                        `"id\_locale",

`                        `"old\_idlocale",

`                        `"nomelocale",

`                        `"descrizione",

`                        `"id\_edificio",

`                        `"id\_piano",

`                        `"old\_id\_edificio",

`                        `"old\_id\_piano",

`                        `"passpartout",

`                        `"is\_laboratorio",

`                        `"is\_radl\_richiesto",

`                        `"is\_user\_richiedibile",

`                        `"note\_locale"

`                `],

`                `"primary\_key\_list": [

`                        `"id\_locale"

`                `],

`                `"references": [

`                        `{

`                                `"to\_table": "location\_edifici",

`                                `"from\_attribute": "id\_edificio",

`                                `"to\_attribute": "id\_edificio",

`                                `"show\_attribute": "nome\_edificio"

`                        `},

`                        `{

`                                `"to\_table": "location\_piani",

`                                `"from\_attribute": "id\_piano",

`                                `"to\_attribute": "id\_piano",

`                                `"show\_attribute": "descrizione\_short"

`                        `}

`                `]

`        `}

In ***references*** si effettua il mapping della chiave esterna indicando la tabella e l'attributo a cui è collegata. In *show\_attribute* si indica un attributo da mostrare al posto della chiave, che può risultare a volte poco significativa.

**Database concept**

Creare un file JSON chiamato db\_concept\_<carattere\_identificativo>.json all'interno di ***Chatidea/resources/db*** e inserire una copia chiamata db\_concept.json all'interno di ***Chatidea/static*** (serve per la webchat)

Il file di concept rappresenta un punto cardine della progettazione, poiché viene utilizzato sia per gestire la conversazione sia per generare le query.

`        `{

`                `"element\_name": "room",

`                `"aliases": ["rooms"],

`                `"type": "secondary",

`                `"table\_name": "location\_locali",

`                `"show\_columns": [

`                        `{

`                                `"keyword": "",

`                                `"columns": ["descrizione"]

`                        `}

`                `],

`                `"category":[],

`                `"attributes": [

`                        `{

`                                `"keyword": "",

`                                `"type": "word",

`                                `"columns": ["descrizione"]

`                        `},

`                        `{

`                                `"keyword": "in building",

`                                `"type": "word",

`                                `"columns": ["nome\_edificio"],

`                                `"by": [

`                                        `{

`                                                `"from\_table\_name": "location\_locali",

`                                                `"from\_columns": ["id\_edificio"],

`                                                `"to\_table\_name": "location\_edifici",

`                                                `"to\_columns": ["id\_edificio"]

`                                        `}

`                                `]

`                        `},

`                        `{

`                                `"keyword": "on floor",

`                                `"type": "word",

`                                `"columns": ["descrizione\_short"],

`                                `"by": [

`                                        `{

`                                                `"from\_table\_name": "location\_locali",

`                                                `"from\_columns": ["id\_piano"],

`                                                `"to\_table\_name": "location\_piani",

`                                                `"to\_columns": ["id\_piano"]

`                                        `}

`                                `]

`                        `}

`                `],

`                `"relations": []

`        `}

**element\_name** indica come ci si deve riferire a una tabella durante la conversazione.

**aliases** indica una serie di alternative che si possono utilizzare al posto dell'element\_name all'interno della conversazione.

**type** definisce il ruolo degli elementi nella conversazione. Una tabella contrassegnata come primary rappresenta un’informazione utile e indipendente dal contesto. Secondary identifica le tabelle i cui dati presi singolarmente non forniscono alcuna informazione, e pertanto per poter accedere ai loro dati si dovrà necessariamente passare da un’altra tabella. Crossable relations serve per contrassegnare le tabelle la cui relazione è molti-a-molti, questo tipo di tabelle infatti di solito presentano solo chiavi di altre tabelle, e senza un opportuno join le informazioni che contiene sarebbero prive di significato.

**show\_columns**. Quando il risultato di una query restituisce più di un risultato il chatbot li mostra in un listato di bottoni. Non essendo fattibile mostrare tutti gli attributi e non essendo la chiave primaria sempre identificativa in linguaggio naturale, bisogna indicare uno o più attributi che andranno mostrati in questa lista e che hanno il compito di rendere chiaro il contenuto del singolo risultato. Questa annotazione va effettuata solo per le tabelle identificate come primary e secondary.

**category**. Per facilitare la navigazione dell'utente si può scegliere di categorizzare in base a una colonna una o più tabelle. Se una tabella primaria ha un attributo il cui valore può essere considerato una categoria da parte del progettista, questo attributo verrà utilizzato per mostrare alcune informazioni di riepilogo sulla tabella.

**attributes**. Permette di definire i qualificatori conversazionali che l'utente può usare durante la conversazione. Il tipo di un qualificatore conversazionale può essere: WORD, NUM o DATE.

**Database view**

Creare un file JSON chiamato db\_view\_<carattere\_identificativo>.json all'interno di ***Chatidea/resources/db***.

`        `"location\_locali": {

`                `"column\_list": [

`                        `{

`                                `"attribute": "descrizione",

`                                `"display": "Name"

`                        `},{

`                                `"attribute": "id\_edificio",

`                                `"display": "Building"

`                        `},{

`                                `"attribute": "id\_piano",

`                                `"display": "Floor"

`                        `},{

`                                `"attribute": "note\_locale",

`                                `"display": "Notes"

`                        `}

`                `]

`        `}

Permette al progettista di indicare quali colonne mostrare di una specifica tabella e di assegnare un alias da mostrare al posto del nome della colonna che spesso risulta non essere significativa in linguaggio naturale.

**Generazione del modello**

Generare il modello chatito con python -m modules.translator. Creare il file db\_concept\_s\_<carattere\_identificativo> che permette di effettuare l'autocompletamento in caso in cui l'utente non specifichi l'elemento di una query. Il progettista, prendendo in riferimento gli attributi generati da chatito, deve classificare le colonne delle tabelle in base a attributi simili. Per esempio, gli attributi che fanno riferimento a un nome di persona fanno parte della stessa categoria, gli attributi che fanno riferimento a un luogo fanno parte di un'altra categoria e così via. Se una colonna non ha similarità con altre colonne non va inserita nella tabella.

[

`    `{

`        `"similars" :    [

`                        `["1\_1","3\_3","5\_3"],

`                        `["1\_2","3\_4","4\_2","5\_4"],

`                        `["1\_3","1\_4"],

`                        `["1\_5", "3\_1"],

`                        `["1\_6", "5\_1"],

`                        `["4\_3", "5\_5"]

`                        `]

`    `}

]

Generare il training set con: cd writer && npx chatito chatito\_model.chatito --format=rasa --defaultDistribution=even Infine addestrare il modello: python -m modules.trainer

