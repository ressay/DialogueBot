import random
import re

class Nlg_system(object):
    def __init__(self) -> None:
        super().__init__()
        self.models = {
            'ask': [
                "Should I <action>?",
                "Do you want me to <action>"
            ],
            'request': {
                'file_not_found': [
                    "I'm sorry, I couldn't find <special_file_name>, maybe you meant something else?",
                    "Sorry, Could you please repeat? I could not find <special_file_name>",
                    "I couldn't find <special_file_name>, did you mean something else? sorry for the inconvenience"
                ],
                'file_name': [
                    "What's the file's name?",
                    "Please give me the file's name",
                    "Can you give me the file's name please?",
                    "What is the name of the file?"
                ],
                'parent_directory': [
                    "What's <file_name>'s parent directory?",
                    "Please give me <file_name>'s parent directory",
                    "Can you give me the parent directory of <file_name> please?",
                    "What is the directory of <file_name>?",
                    "Where is <file_name> located?"
                ],
                'multiple_file_found': [
                    "I found many files named <file_name>, could you please tell me what's its parent directory?",
                    "I found many files '<file_name>', Please give me its parent directory?",
                    "Sorry I can't tell which '<file_name>' you meant, could you tell me where is it located?"
                ],
                'dest': [
                    "Where do you want me to put <file_name>?",
                    "Please give me <file_name>'s destination",
                    "Can you please provide <file_name>'s destination?",
                    "To which destination?",
                    "Where should I put <file_name>?",
                    "Where to?"
                ]
            },
            'Create_file': [
                '<file_type> <file_name> has been created!',
                'I created <file_type> <file_name> in <path>',
                '<path> now contains <file_name>!',
                '<file_type> <file_name> has been created under <path>',
                'I created a <file_type> <file_name>',
                'I created <file_type> <file_name> in <path>'
            ],
            'Delete_file': [
                '<file_type> <file_name> has been removed!',
                'I deleted <file_type> <file_name> from <path>',
                '<file_type> <file_name> has been deleted from <path>',
                'I removed <file_name>',
                'I removed <file_type> <file_name> from <path>'
            ],
            'Move_file': [
                'I moved <file_name> from <origin> to <dest>',
                '<file_name> has been moved from <origin> to <dest>',
                'I moved <file_name> to <dest>',
            ],
            'Copy_file': [
                'I copied <file_name> from <origin> to <dest>',
                '<file_name> has been copied from <origin> to <dest>',
                'I copied <file_name> to <dest>',
            ],
            'Change_directory': [
                'Changed directory to <new_directory>',
                'I moved to <new_directory>',
                "We're in <new_directory> now!",
                "I moved to path <new_directory>"
            ],
            'inform': [
                "file path is <path>"
            ],
            'default': [
                "Sorry, can you repeat, I did not understand",
                "Hmmm, I failed to understand",
                "Sorry?",
                "Could you please repeat? I did not understand"
            ]
        }
        self.expressions = {
            'file_name': ['<value>'],
            'new_directory': ['<value>'],
            'dest': ['<value>'],
            'origin': ['<value>'],
            'file_type': ['<value>'],
            'path': ['<value>'],
            'special_file_name': ['<value>']
        }
        self.actions = {
            'request': [
                'request something'
            ],
            'Create_file': [
                'create <file_type> <file_name> under <path>'
            ],
            'Delete_file': [
                'delete <file_type> <file_name> from <path>'

            ],
            'Move_file': [
                'move <file_name> from <origin> to <dest>'
            ],
            'Copy_file': [
                'copy <file_name> from <origin> to <dest>'
            ],
            'Change_directory': [
                'change directory to <new_directory>'
            ],
            'inform': [
                "inform you"
            ]
        }

    def action_expression(self, action):
        models = self.actions[action['intent']]
        result = []
        for model in models:
            for param in re.findall('<(.+?)>', model):
                expressions = self.get_expressions(param, action[param])
                e = self.choose_random(expressions)
                model = model.replace('<'+param+'>', e)
            result.append(model)
        return result

    def get_expressions(self, key, value):
        if key == 'action':
            return self.action_expression(value)
        tab = self.expressions[key]
        return [sentence.replace('<value>', value) for sentence in tab]

    def get_models(self, agent_action):
        intent = agent_action['intent']
        if intent == 'request':
            if 'special' in agent_action:
                return self.models[intent][agent_action['special']]
            return self.models[intent][agent_action['slot']]
        return self.models[intent]

    def choose_random(self,tab):
        return tab[random.randint(0,len(tab)-1)]

    def get_sentence(self, agent_action):
        models = self.get_models(agent_action)
        model = self.choose_random(models)
        for param in re.findall('<(.+?)>',model):
            expressions = self.get_expressions(param,agent_action[param])
            e = self.choose_random(expressions)
            model = model.replace('<'+param+'>', e)
        return model


if __name__ == '__main__':
    nlg = Nlg_system()
    print(nlg.get_sentence({'intent': 'request', 'slot': 'parent_directory',
                            'file_name': 'khobz file',
                            'special': 'multiple_file_found'}))
    print(nlg.get_sentence({'intent': 'Change_directory',
                            'new_directory': 'esta/lavida/baby'}))
    print(nlg.get_sentence({'intent': 'ask', 'action': {'intent': 'Create_file', 'file_name': 'khobz',
                            'path': 'eso/es', 'file_type': 'file'}}))

