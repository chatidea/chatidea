import logging

from rasa.nlu import training_data as nlu_train
from rasa.nlu import model as nlu_model
from rasa.nlu import config
from settings import NLU_MODEL_DIR_PATH, NLU_CONFIG_PIPELINE, NLU_CONFIG_LANGUAGE, NLU_DATA_PATH, NLU_MODEL_PATH

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('NLU model:\n'
                 '"' + NLU_MODEL_PATH + '"')
    logging.info('Training the NLU model...')
    training_data = nlu_train.load_data(NLU_DATA_PATH)
    trainer = nlu_model.Trainer(config.RasaNLUModelConfig({"pipeline": NLU_CONFIG_PIPELINE,
                                                                     "language": NLU_CONFIG_LANGUAGE}))
    trainer.train(training_data)
    model_directory = trainer.persist(NLU_MODEL_DIR_PATH, fixed_model_name='nlu_model')
    logging.info('NLU model completely trained!')

"""
complex pipeline:

pipeline = [{"name": "nlp_spacy"},
            {"name": "tokenizer_spacy"},
            {"name": "intent_entity_featurizer_regex"},
            {"name": "intent_featurizer_spacy"},
            {"name": "ner_crf"},
            {"name": "ner_synonyms"},
            {"name": "intent_classifier_sklearn"}]

pipeline = [{"name": "tokenizer_whitespace"},
            {"name": "ner_crf"},
            {"name": "ner_synonyms"},
            {"name": "intent_featurizer_count_vectors"},
            {"name": "intent_classifier_tensorflow_embedding"}]

"""