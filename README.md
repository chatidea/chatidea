# **Chatidea**

Chatidea è un framework che permette di generare chatbot partendo dallo schema di una base di dati.

**Requisiti ed esecuzione chatbot**

- [Python 3.7.6](https://www.python.org/downloads/release/python-376/)
- [Node.js](https://nodejs.org/it/)
- Installare chatito mediante il comando: _ **npm i chatito –save** _
- Installare il gestore delle dipendenze PIP: se non si ha nessuna versione di pip installata bisogna prima scaricare il file [get-pip.py](https://bootstrap.pypa.io/get-pip.py) e lanciare il seguente comando dalla cartella dove avete scaricato il file:
_ **python get-pip.py** _
- Gestore delle dipendenze e ambienti virtuali installabile con comando
_ **py -3.7 -m pip install pipenv** _(in ambiente UNIX il comando _ **py** _ viene sostituito dal comando _ **python3** __;_ se su windows non dovesse funzionare il comando _ **py** _ provare con _ **python** _)
- Per installare tutte le dipendenze necessarie è sufficiente posizionarsi nella cartella Chatidea e lanciare i seguenti comandi in sequenza:
_**SET PIPENV\_VENV\_IN\_PROJECT=1
 pipenv install**_
- Prima di lanciare il chatbot ricordare di avere sul proprio sistema attivo MySql e di aver installato il database di riferimento del chatbot ( **deib** nel caso corrente il cui dump è disponibile nella cartella _Chatidea\resources\db_). Seguire gli step della configurazione per collegare il chatbot al database
- Per lanciare la chatbot dalla cartella Chatidea eseguire il comando
_ **pipenv run python run.py** _
- Dal browser ora il chabot è raggiungibile all&#39;indirizzo _ **localhost:5080** _

**NB:** In Windows potrebbero verificarsi problemi nell&#39;installazione della dipendenza ujson. Per risolvere tale problema bisogna installare gli strumenti per VC++ del sistema operativo. Per fare questo, scaricare [_Microsoft Build Tools 2015_](https://visualstudio.microsoft.com/it/thank-you-downloading-visual-studio/?sku=BuildTools&amp;rel=16)
Far partire l&#39;installazione, al termine spuntare la casella &quot;Strumenti di compilazione C++&quot; e selezionare i seguenti strumenti:

![](RackMultipart20210216-4-vyf99n_html_88c8875048150d7a.png)

Dopo aver selezionato tutti questi componenti procedere con l&#39;installazione. A installazione terminata, tornare nel prompt dei comandi e lanciare:

  1. SET PIPENV\_VENV\_IN\_PROJECT=1
  2. pipenv install

**Configurazione**

Le variabili di configurazione sono all&#39;interno di _ **Chatidea/settings.py** _

![](RackMultipart20210216-4-vyf99n_html_b8caa7ae3882eec.gif)

select =&#39;deib&#39;

select\_dict = {

&#39;teachers&#39;: [&#39;b&#39;, &#39;teachers&#39;, &#39;797397572:AAEV1MfR28lTzPsom\_2qO2-goJSCKzQZ5d0&#39;],

&#39;classicmodels&#39;: [&#39;c&#39;, &#39;classicmodels&#39;, &#39;710759393:AAGcrq2gkBd84qa-apwS9quMd5QK0knfWTM&#39;],

&#39;deib&#39;: [&#39;d&#39;, &#39;deib&#39;, &#39;1046778538:AAF2CKzjxwzCu9fiDLgadBujYKuBKhgKmdE&#39;]

}

_ **select\_dict** _ contiene una lista di database, è composto da: un carattere identificativo, il nome dello schema, l&#39;API Key del bot telegram. _ **select** _ contiene il nome del database attualmente in uso.

![](RackMultipart20210216-4-vyf99n_html_b8caa7ae3882eec.gif)

remote =Trueif os.environ.get(&#39;PYTHONANYWHERE\_SITE&#39;) elseFalse

DATABASE\_USER=&#39;nicolacastaldo&#39;if remote else&#39;root&#39;

DATABASE\_PASSWORD=&#39;dataexplorerbot&#39;if remote else&#39;&#39;

DATABASE\_HOST=&#39;nicolacastaldo.mysql.pythonanywhere-services.com&#39;if remote else&#39;localhost&#39;

DATABASE\_NAME=&#39;nicolacastaldo$classicmodels&#39;if remote else db\_name

Cambiare user e password locali con i propri dati e, nel caso si voglia utilizzare un host remoto, modificare opportunamente la variabile d&#39;ambiente e i dati restanti.

**Configurazione Webchat**

In caso di utilizzo di  **https**  usare la parte di codice commentata e inserire certificato e private key in _ **Chatidea/modules/connectors** _.

#sio = socketio.AsyncServer(cors\_allowed\_origins=[]) #Only for SSL workaround so that socketio works with requests from other origins.

sio = socketio.AsyncServer()

defstart():

#cert\_path = os.path.dirname(os.path.realpath(\_\_file\_\_))

#context = ssl.create\_default\_context(purpose=ssl.Purpose.CLIENT\_AUTH)

#context.load\_cert\_chain(certfile=cert\_path+ &quot;/certificate.crt&quot;, keyfile= cert\_path+&quot;/private.key&quot;)

#web.run\_app(app, port=5080,ssl\_context=context)

web.run\_app(app, port=5080)

Ricordare di cambiare il  **socketUrl**  dentro _ **Chatidea/modules/connectors/index.html** _ inserendo http o https e la porta giusta.

![](RackMultipart20210216-4-vyf99n_html_b8caa7ae3882eec.gif)

La libreria utilizzata per gestire la webchat non sembra più raggiungibile. In alternativa potete usare:

\&lt;scriptsrc=&quot;https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.min.js&quot;\&gt;\&lt;/script\&gt;

Al posto di:

\&lt;scriptsrc=&quot;https://storage.googleapis.com/mrbot-cdn/webchat-0.5.3.js&quot;\&gt;\&lt;/script\&gt;

è necessario però modificare le personalizzazioni effettuate precedentemente in  **index.html**  adattandole alla nuova libreria.

**Come far partire il chatbot**

Dentro  **Chatidea/run.py**  decommentare in base all&#39;ambiente in cui si vuole eseguire il chatbot.

webchat.start()

#telegram.start()

#console\_input()

In  **locale**  posizionatevi dentro _ **Chatidea** _ e eseguite il comando python run.py

Per farlo partire in  **remoto**  sul server uniba utilizzare  **tmux**  per non far terminare l&#39;esecuzione dello script a sessione finita tmux new -s \&lt;nome-sessione\&gt; python run.py

Per riprendere il controllo della console dopo che si è usciti: tmux attach -t \&lt;nome-sessione\&gt;

**Fasi per la generazione di un chatbot**

Il processo di creazione di un nuovo chatbot può essere visto come una procedura semi-automatica, essendo costituita da azioni automatiche e manuali. Le azioni manuali sono quelle che dovranno essere svolte dal progettista e sono quelle che interessano l&#39;annotazione dei dati.

**Database schema**

Creare un file JSON chiamato db\_schema\_\&lt;carattere\_identificativo\&gt;.json all&#39;interno di _ **Chatidea/resources/db** _. Il file contiene una descrizione semplificata del database, evidenziandone la struttura in termini di attributi e relazioni.

Esempio di come descrivere una tabella:

&quot;location\_locali&quot;: {

&quot;column\_list&quot;: [

&quot;id\_locale&quot;,

&quot;old\_idlocale&quot;,

&quot;nomelocale&quot;,

&quot;descrizione&quot;,

&quot;id\_edificio&quot;,

&quot;id\_piano&quot;,

&quot;old\_id\_edificio&quot;,

&quot;old\_id\_piano&quot;,

&quot;passpartout&quot;,

&quot;is\_laboratorio&quot;,

&quot;is\_radl\_richiesto&quot;,

&quot;is\_user\_richiedibile&quot;,

&quot;note\_locale&quot;

],

&quot;primary\_key\_list&quot;: [

&quot;id\_locale&quot;

],

&quot;references&quot;: [

{

&quot;to\_table&quot;: &quot;location\_edifici&quot;,

&quot;from\_attribute&quot;: &quot;id\_edificio&quot;,

&quot;to\_attribute&quot;: &quot;id\_edificio&quot;,

&quot;show\_attribute&quot;: &quot;nome\_edificio&quot;

},

{

&quot;to\_table&quot;: &quot;location\_piani&quot;,

&quot;from\_attribute&quot;: &quot;id\_piano&quot;,

&quot;to\_attribute&quot;: &quot;id\_piano&quot;,

&quot;show\_attribute&quot;: &quot;descrizione\_short&quot;

}

]

}

In _ **references** _ si effettua il mapping della chiave esterna indicando la tabella e l&#39;attributo a cui è collegata. In _show\_attribute_ si indica un attributo da mostrare al posto della chiave, che può risultare a volte poco significativa.

**Database concept**

Creare un file JSON chiamato db\_concept\_\&lt;carattere\_identificativo\&gt;.json all&#39;interno di _ **Chatidea/resources/db** _ e inserire una copia chiamata db\_concept.json all&#39;interno di _ **Chatidea/static** _ (serve per la webchat)

Il file di concept rappresenta un punto cardine della progettazione, poiché viene utilizzato sia per gestire la conversazione sia per generare le query.

{

&quot;element\_name&quot;: &quot;room&quot;,

&quot;aliases&quot;: [&quot;rooms&quot;],

&quot;type&quot;: &quot;secondary&quot;,

&quot;table\_name&quot;: &quot;location\_locali&quot;,

&quot;show\_columns&quot;: [

{

&quot;keyword&quot;: &quot;&quot;,

&quot;columns&quot;: [&quot;descrizione&quot;]

}

],

&quot;category&quot;:[],

&quot;attributes&quot;: [

{

&quot;keyword&quot;: &quot;&quot;,

&quot;type&quot;: &quot;word&quot;,

&quot;columns&quot;: [&quot;descrizione&quot;]

},

{

&quot;keyword&quot;: &quot;in building&quot;,

&quot;type&quot;: &quot;word&quot;,

&quot;columns&quot;: [&quot;nome\_edificio&quot;],

&quot;by&quot;: [

{

&quot;from\_table\_name&quot;: &quot;location\_locali&quot;,

&quot;from\_columns&quot;: [&quot;id\_edificio&quot;],

&quot;to\_table\_name&quot;: &quot;location\_edifici&quot;,

&quot;to\_columns&quot;: [&quot;id\_edificio&quot;]

}

]

},

{

&quot;keyword&quot;: &quot;on floor&quot;,

&quot;type&quot;: &quot;word&quot;,

&quot;columns&quot;: [&quot;descrizione\_short&quot;],

&quot;by&quot;: [

{

&quot;from\_table\_name&quot;: &quot;location\_locali&quot;,

&quot;from\_columns&quot;: [&quot;id\_piano&quot;],

&quot;to\_table\_name&quot;: &quot;location\_piani&quot;,

&quot;to\_columns&quot;: [&quot;id\_piano&quot;]

}

]

}

],

&quot;relations&quot;: []

}

**element\_name**  indica come ci si deve riferire a una tabella durante la conversazione.

**aliases**  indica una serie di alternative che si possono utilizzare al posto dell&#39;element\_name all&#39;interno della conversazione.

**type**  definisce il ruolo degli elementi nella conversazione. Una tabella contrassegnata come primary rappresenta un&#39;informazione utile e indipendente dal contesto. Secondary identifica le tabelle i cui dati presi singolarmente non forniscono alcuna informazione, e pertanto per poter accedere ai loro dati si dovrà necessariamente passare da un&#39;altra tabella. Crossable relations serve per contrassegnare le tabelle la cui relazione è molti-a-molti, questo tipo di tabelle infatti di solito presentano solo chiavi di altre tabelle, e senza un opportuno join le informazioni che contiene sarebbero prive di significato.

**show\_columns**. Quando il risultato di una query restituisce più di un risultato il chatbot li mostra in un listato di bottoni. Non essendo fattibile mostrare tutti gli attributi e non essendo la chiave primaria sempre identificativa in linguaggio naturale, bisogna indicare uno o più attributi che andranno mostrati in questa lista e che hanno il compito di rendere chiaro il contenuto del singolo risultato. Questa annotazione va effettuata solo per le tabelle identificate come primary e secondary.

**category**. Per facilitare la navigazione dell&#39;utente si può scegliere di categorizzare in base a una colonna una o più tabelle. Se una tabella primaria ha un attributo il cui valore può essere considerato una categoria da parte del progettista, questo attributo verrà utilizzato per mostrare alcune informazioni di riepilogo sulla tabella.

**attributes**. Permette di definire i qualificatori conversazionali che l&#39;utente può usare durante la conversazione. Il tipo di un qualificatore conversazionale può essere: WORD, NUM o DATE.

**Database view**

Creare un file JSON chiamato db\_view\_\&lt;carattere\_identificativo\&gt;.json all&#39;interno di _ **Chatidea/resources/db** _.

&quot;location\_locali&quot;: {

&quot;column\_list&quot;: [

{

&quot;attribute&quot;: &quot;descrizione&quot;,

&quot;display&quot;: &quot;Name&quot;

},{

&quot;attribute&quot;: &quot;id\_edificio&quot;,

&quot;display&quot;: &quot;Building&quot;

},{

&quot;attribute&quot;: &quot;id\_piano&quot;,

&quot;display&quot;: &quot;Floor&quot;

},{

&quot;attribute&quot;: &quot;note\_locale&quot;,

&quot;display&quot;: &quot;Notes&quot;

}

]

}

Permette al progettista di indicare quali colonne mostrare di una specifica tabella e di assegnare un alias da mostrare al posto del nome della colonna che spesso risulta non essere significativa in linguaggio naturale.

**Generazione del modello**

Generare il modello chatito con python -m modules.translator. Creare il file db\_concept\_s\_\&lt;carattere\_identificativo\&gt; che permette di effettuare l&#39;autocompletamento in caso in cui l&#39;utente non specifichi l&#39;elemento di una query. Il progettista, prendendo in riferimento gli attributi generati da chatito, deve classificare le colonne delle tabelle in base a attributi simili. Per esempio, gli attributi che fanno riferimento a un nome di persona fanno parte della stessa categoria, gli attributi che fanno riferimento a un luogo fanno parte di un&#39;altra categoria e così via. Se una colonna non ha similarità con altre colonne non va inserita nella tabella.

[

{

&quot;similars&quot; : [

[&quot;1\_1&quot;,&quot;3\_3&quot;,&quot;5\_3&quot;],

[&quot;1\_2&quot;,&quot;3\_4&quot;,&quot;4\_2&quot;,&quot;5\_4&quot;],

[&quot;1\_3&quot;,&quot;1\_4&quot;],

[&quot;1\_5&quot;, &quot;3\_1&quot;],

[&quot;1\_6&quot;, &quot;5\_1&quot;],

[&quot;4\_3&quot;, &quot;5\_5&quot;]

]

}

]

Generare il training set con: cd writer &amp;&amp; npx chatito chatito\_model.chatito --format=rasa --defaultDistribution=even Infine addestrare il modello: python -m modules.trainer