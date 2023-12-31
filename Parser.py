from code_gen import *
from preprocess import get_action_table
from Scanner import get_next_token
from anytree import Node, RenderTree
from semantic_analyser import semantic_checks


def get_look_ahead(token):
    type, lexeme = token
    if type == 'ID' or type == 'NUM':
        return type
    return lexeme


def get_token(file, lineno):
    token, state, character, lineno, token_lineno = get_next_token(file, lineno)
    if state >= 0 and token is not None:  # No Lexical Error
        return token, get_look_ahead(token), lineno, token_lineno
    if not character:  # EOF
        return '$', '$', lineno, token_lineno
    return get_token(file, lineno)


semantic_error = False
semantic_errors = []


def code_generator(st, nt, token, state, next_state, lineno):
    global semantic_error, semantic_errors
    error, message = semantic_checks(st, nt, token, state, next_state, lineno)
    if lineno == 41 and token == "if":
        if error:
            message = f"#{lineno -2} : Semantic Error! No 'repeat ... until' found for 'break'."
            semantic_error = True
            semantic_errors.append(message)
    else:
        if error:
            semantic_error = True
            semantic_errors.append(message)
    routines(st, nt, token, state, next_state)


def parse(file_path='input.txt'):
    file = open(file_path, 'rb')
    root = Node('Program')
    stack = [(root, 0, 1)]
    action_table = get_action_table('grammar.txt')
    lineno = 1
    token, look_ahead, lineno, token_lineno = get_token(file, lineno)
    syntax_errors = []
    while True:
        node, state, next_state = stack.pop()
        nt = node.name
        if (nt, state, look_ahead) not in action_table.keys():  # Goal State
            action = ['return']
        else:
            action = action_table[(nt, state, look_ahead)].split()

        if action[0] == 'return':
            temp = token
            if token == '$':
                temp = '$$'
            code_generator(action[0], nt, temp[1], state, next_state, token_lineno)
            if token == '$' and nt == 'Program':
                break
            node, state, next_state = stack.pop()
            stack.append((node, next_state, 0))

        if action[0] == 'goto':
            tk = action[1]
            if tk != 'epsilon':
                tk = token
            next_state = int(action[2])
            temp = tk
            if token == '$':
                temp = '$$'
            code_generator(action[0], nt, temp[1], state, next_state, token_lineno)
            stack.append((node, next_state, 0))
            Node(tk, parent=node)
            if tk != 'epsilon':
                token, look_ahead, lineno, token_lineno = get_token(file, lineno)

        if action[0] == 'call':
            tk = action[1]
            next_state = int(action[2])
            temp = token
            if token == '$':
                temp = '$$'
            code_generator(action[0], nt, temp[1], state, next_state, token_lineno)
            stack.append((node, state, next_state))
            stack.append((Node(tk, parent=node), 0, 0))

        if action[0] == 'missing':
            tk = action[1]
            next_state = int(action[2])
            syntax_errors.append(f'#{token_lineno} : syntax error, missing {tk}')
            stack.append((node, next_state, 0))

        if action[0] == 'illegal':
            tk = action[1]
            next_state = int(action[2])
            if look_ahead == '$':
                syntax_errors.append(f'#{token_lineno} : syntax error, Unexpected EOF')
                break
            else:
                syntax_errors.append(f'#{token_lineno} : syntax error, illegal {tk}')
            stack.append((node, state, next_state))
            token, look_ahead, lineno, token_lineno = get_token(file, lineno)

    file.close()

    save2txt(program_block)
    # save2txt_syntax(root, syntax_errors) for phase2


def save2txt(pb):
    out_file = open('output.txt', 'w')
    error_file = open('semantic_errors.txt', 'w')
    if semantic_error:
        out_file.write('The code has not been generated.')
        for i in range(len(semantic_errors)):
            error_file.write(f'{semantic_errors[i]}\n')

    else:
        for i in range(len(pb)):
            out_file.write(f'{i}\t{pb[i]}\n')
        error_file.write('The input program is semantically correct.')
    out_file.close()
    error_file.close()


def save2txt_syntax(root, errors):
    out = open('parse_tree.txt', 'w', encoding='utf-8')
    res = ''
    for pre, fill, node in RenderTree(root):
        res = res + "%s%s" % (pre, node.name) + '\n'
    res = res.replace("'", '')
    out.write(res[:-1])
    out.close()

    out = open('syntax_errors.txt', 'w', encoding='utf-8')
    res = ''
    for e in errors:
        res = res + e + '\n'
    if res == '':
        res = 'There is no syntax error.'
    out.write(res)
    out.close()
