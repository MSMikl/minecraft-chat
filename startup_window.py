import tkinter as tk

import configparser

from tkinter import ttk, messagebox


def save_and_launch(window, config, name, key):
    if not (key or name):
        messagebox.showerror('Невозможно запустить чат', 'Укажите токен для входа или имя пользователя для регистрации')
        return
    config['CONNECTION']['nickname'] = name
    config['CONNECTION']['key'] = key
    with open('config.ini', 'w') as file:
        config.write(file)
    window.destroy()


def show_startup_window():
    config = configparser.ConfigParser()
    config.read('config.ini')
    window = tk.Tk()
    window.title('Запуск чата')
    window.geometry('500x300')
    window.attributes("-toolwindow", True)
    frame = ttk.Frame()
    frame.pack(expand=True)

    text = """
    Приветствуем в чате Minecraft.
    Для запуска чата введите имя пользователя для регистрации
    или имеющийся у вас токен для входа под имеющимся логином
    """
    description_label = ttk.Label(frame, text=text, justify='center')
    description_label.grid(row=1, column=1, columnspan=3)

    name_label = ttk.Label(frame, text='Имя пользователя')
    name_label.grid(row=2, column=1, sticky='w', padx=3, pady=10)
    name_value = tk.StringVar()
    name_value.set(config['CONNECTION']['nickname'])
    name_entry = ttk.Entry(frame, textvariable=name_value, justify='right')
    name_entry.grid(row=2, column=3)

    key_label = ttk.Label(frame, text='Токен пользователя')
    key_label.grid(row=3, column=1, sticky='w', padx=3, pady=10)
    key_value = tk.StringVar()
    key_value.set(config['CONNECTION']['key'])
    key_entry = ttk.Entry(frame, textvariable=key_value, justify='right')
    key_entry.grid(row=3, column=3)

    launch_button = ttk.Button(
        frame,
        text='Запустить чат',
        command=lambda: save_and_launch(
            window,
            config,
            name_value.get(),
            key_value.get(),
        )
    )
    launch_button.grid(row=4, column=2, padx=3, pady=10)

    window.mainloop()


if __name__ == '__main__':
    show_startup_window()