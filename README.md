# Sherbot
Sherbot è un framework che permette di generare chatbot partendo dallo schema di una base di dati.


## Requisiti
- [Python 3.7.6]( https://www.python.org/downloads/release/python-376/ "Python 3.7.6")
-  pip 20.0.2. 
` pip install pip==20.0.2`
Se non si ha nessuna versione di pip installata bisogna prima scaricare il file [get-pip.py](https://bootstrap.pypa.io/get-pip.py "get-pip.py") e  lanciare:
`python get-pip.py`
- Per installare tutte le dipendenze necessarie è sufficiente posizionarsi nella cartella **sherbot** e lanciare:
`pip install -r requirements.txt`
- [Node.js](https://nodejs.org/it/ "Node.js")
- Chatito: `npm i chatito --save`


## Configurazione
Le variabili di configurazione sono all'interno di ***sherbot/settings.py***

------------



```python
select = 'deib'

select_dict = {
    'teachers': ['b', 'teachers', '797397572:AAEV1MfR28lTzPsom_2qO2-goJSCKzQZ5d0'],
    'classicmodels': ['c', 'classicmodels', '710759393:AAGcrq2gkBd84qa-apwS9quMd5QK0knfWTM'],
    'deib': ['d', 'deib', '1046778538:AAF2CKzjxwzCu9fiDLgadBujYKuBKhgKmdE']
}
```
***select_dict*** contiene una lista di database, è composto da: un carattere identificativo, il nome dello schema, l'API Key del bot telegram.
***select*** contiene il nome del database attualmente in uso.

------------

```python
remote = True if os.environ.get('PYTHONANYWHERE_SITE') else False

DATABASE_USER = 'nicolacastaldo' if remote else 'root'
DATABASE_PASSWORD = 'dataexplorerbot' if remote else ''
DATABASE_HOST = 'nicolacastaldo.mysql.pythonanywhere-services.com' if remote else 'localhost'
DATABASE_NAME = 'nicolacastaldo$classicmodels' if remote else db_name

```
Cambiare user e password locali con i propri dati e, nel caso si voglia utilizzare un host remoto, modificare opportunamente la variabile d'ambiente e i dati restanti.

### Configurazione Webchat
In caso di utilizzo di **https** usare la parte di codice commentata e inserire certificato e private key in ***sherbot/modules/connectors***.
```python
#sio = socketio.AsyncServer(cors_allowed_origins=[]) #Only for SSL workaround so that socketio works with requests from other origins.
sio = socketio.AsyncServer()
```
```python
def start():
    #cert_path = os.path.dirname(os.path.realpath(__file__))
    #context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    #context.load_cert_chain(certfile=cert_path+ "/certificate.crt", keyfile= cert_path+"/private.key")
    #web.run_app(app, port=5080,ssl_context=context)
    web.run_app(app, port=5080)
```

Ricordare di cambiare il **socketUrl** dentro ***sherbot/modules/connectors/index.html*** inserendo http o https e la porta giusta.

------------
La libreria utilizzata per gestire la webchat non sembra più raggiungibile. In alternativa potete usare:
```javascript
<script src="https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.min.js"></script>
```
Al posto di:

```javascript
<script src="https://storage.googleapis.com/mrbot-cdn/webchat-0.5.3.js"></script>
```
è necessario però modificare le personalizzazioni effettuate precedentemente in **index.html** adattandole alla nuova libreria.

## Come far partire il chatbot
Dentro **sherbot/run.py** decommentare in base all'ambiente in cui si vuole eseguire il chatbot.
```python
    webchat.start()
    #telegram.start()
    #console_input()
```

In **locale** posizionatevi dentro ***Sherbot*** e eseguite il comando
`python run.py`

Per farlo partire in **remoto** sul server uniba utilizzare **tmux** per non far terminare l'esecuzione dello script a sessione finita
`tmux new -s <nome-sessione>`
`python run.py`

Per riprendere il controllo della console dopo che si è usciti:
`tmux attach -t <nome-sessione>`

## Fasi per la generazione di un chatbot
Il processo di creazione di un nuovo chatbot può essere visto come una procedura
semi-automatica, essendo costituita da azioni automatiche e manuali. Le azioni
manuali sono quelle che dovranno essere svolte dal progettista e sono quelle che
interessano l’annotazione dei dati.
### Database schema
Creare un file JSON chiamato `db_schema_<carattere_identificativo>.json` all'interno di ***sherbot/resources/db***. Il file contiene una descrizione semplificata del database, evidenziandone la struttura in termini di attributi e relazioni.

Esempio di come descrivere una tabella:
```json
        "location_locali": {
                "column_list": [
                        "id_locale",
                        "old_idlocale",
                        "nomelocale",
                        "descrizione",
                        "id_edificio",
                        "id_piano",
                        "old_id_edificio",
                        "old_id_piano",
                        "passpartout",
                        "is_laboratorio",
                        "is_radl_richiesto",
                        "is_user_richiedibile",
                        "note_locale"
                ],
                "primary_key_list": [
                        "id_locale"
                ],
                "references": [
                        {
                                "to_table": "location_edifici",
                                "from_attribute": "id_edificio",
                                "to_attribute": "id_edificio",
                                "show_attribute": "nome_edificio"
                        },
                        {
                                "to_table": "location_piani",
                                "from_attribute": "id_piano",
                                "to_attribute": "id_piano",
                                "show_attribute": "descrizione_short"
                        }
                ]
        }
```
In ***references*** si effettua il mapping della chiave esterna indicando la tabella e l'attributo a cui è collegata. In *show_attribute* si indica un attributo da mostrare al posto della chiave, che può risultare a volte poco significativa.

### Database concept
Creare un file JSON chiamato `db_concept_<carattere_identificativo>.json` all'interno di ***sherbot/resources/db*** e inserire una copia chiamata `db_concept.json`  all'interno di ***sherbot/static*** (serve per la webchat)

Il file di concept rappresenta un punto cardine della progettazione, poiché viene
utilizzato sia per gestire la conversazione sia per generare le query.
```json
        {
                "element_name": "room",
                "aliases": ["rooms"],
                "type": "secondary",
                "table_name": "location_locali",
                "show_columns": [
                        {
                                "keyword": "",
                                "columns": ["descrizione"]
                        }
                ],
                "category":[],
                "attributes": [
                        {
                                "keyword": "",
                                "type": "word",
                                "columns": ["descrizione"]
                        },
                        {
                                "keyword": "in building",
                                "type": "word",
                                "columns": ["nome_edificio"],
                                "by": [
                                        {
                                                "from_table_name": "location_locali",
                                                "from_columns": ["id_edificio"],
                                                "to_table_name": "location_edifici",
                                                "to_columns": ["id_edificio"]
                                        }
                                ]
                        },
                        {
                                "keyword": "on floor",
                                "type": "word",
                                "columns": ["descrizione_short"],
                                "by": [
                                        {
                                                "from_table_name": "location_locali",
                                                "from_columns": ["id_piano"],
                                                "to_table_name": "location_piani",
                                                "to_columns": ["id_piano"]
                                        }
                                ]
                        }
                ],
                "relations": []
        }
```

**element_name** indica come ci si deve riferire a una tabella durante la conversazione.

**aliases** indica una serie di alternative che si possono utilizzare al posto dell'element_name all'interno della conversazione.

**type** definisce il ruolo degli elementi nella conversazione. Una tabella contrassegnata come primary rappresenta un’informazione utile e indipendente dal contesto. Secondary  identifica le tabelle i cui dati presi singolarmente non forniscono alcuna informazione, e pertanto per poter accedere ai loro dati si dovrà necessariamente passare da un’altra tabella. Crossable relations serve per contrassegnare le tabelle la cui relazione è molti-a-molti, questo tipo di tabelle infatti di solito presentano solo chiavi di altre tabelle, e senza un opportuno join le informazioni che contiene sarebbero prive di significato.

**show_columns**. Quando il risultato di una query restituisce più di un risultato il chatbot li mostra in un listato di bottoni. Non essendo fattibile mostrare tutti gli attributi e non essendo la chiave primaria sempre identificativa in linguaggio naturale, bisogna indicare uno o più attributi che andranno mostrati in questa lista e che hanno il compito di rendere chiaro il contenuto del singolo risultato. Questa annotazione va effettuata solo per le tabelle identificate come primary e secondary.

**category**. Per facilitare la navigazione dell'utente si può scegliere di categorizzare in base a una colonna una o più tabelle. Se una tabella primaria ha un attributo il cui valore può essere considerato una categoria da parte del progettista, questo attributo verrà utilizzato per mostrare alcune informazioni di riepilogo sulla tabella.

**attributes**. Permette di definire i qualificatori conversazionali che l'utente può usare durante la conversazione. Il tipo di un qualificatore conversazionale può essere: WORD, NUM o DATE.

### Database view
Creare un file JSON chiamato `db_view_<carattere_identificativo>.json` all'interno di ***sherbot/resources/db***.
```json
        "location_locali": {
                "column_list": [
                        {
                                "attribute": "descrizione",
                                "display": "Name"
                        },{
                                "attribute": "id_edificio",
                                "display": "Building"
                        },{
                                "attribute": "id_piano",
                                "display": "Floor"
                        },{
                                "attribute": "note_locale",
                                "display": "Notes"
                        }
                ]
        }
```
Permette al progettista di indicare quali colonne mostrare di una specifica tabella e di assegnare un alias da mostrare al posto del nome della colonna che spesso risulta non essere significativa in linguaggio naturale.

### Generazione del modello
Generare il modello chatito con `python -m modules.translator`. 
Creare il file `db_concept_s_<carattere_identificativo>` che permette di effettuare l'autocompletamento in caso in cui l'utente non specifichi l'elemento di una query.  Il progettista, prendendo in riferimento gli attributi generati da chatito, deve classificare le colonne delle tabelle in base a attributi simili. Per esempio, gli attributi che fanno riferimento a un nome di persona fanno parte della stessa categoria, gli attributo che fanno riferimento a un luogo fanno parte di un'altra categoria e così via. Se una colonna non ha similarità con altre colonne non va inserita nella tabella.
```json
[
    {
        "similars" :    [
                        ["1_1","3_3","5_3"],
                        ["1_2","3_4","4_2","5_4"],
                        ["1_3","1_4"],
                        ["1_5", "3_1"],
                        ["1_6", "5_1"],
                        ["4_3", "5_5"]
                        ]
    }
]
```
Generare il training set con:
`cd writer && npx chatito chatito_model.chatito --format=rasa --defaultDistribution=even`
Infine addestrare il modello:
`python -m modules.trainer`







