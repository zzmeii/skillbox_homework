#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#

from twisted.internet import reactor
from twisted.internet.protocol import connectionDone, ServerFactory
from twisted.protocols.basic import LineOnlyReceiver


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""
    
    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI
    
    # указание фабрики для обработки подключений
    factory: 'Server'
    
    # информация о клиенте
    ip: str
    login: str = None
    
    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """
        
        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики
        
        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера
    
    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """
        
        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике
        
        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера
    
    def connection_lose(self):
        self.transport.loseConnection()
    
    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """
        
        message = line.decode()  # раскодируем полученное сообщение в строку
        
        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:
                login = message.replace("login:", "")  # вырезаем часть после :
                for user in self.factory.clients:
                    if login == user.login:
                        print(f"{self.ip}: попытка авторизации с уже авторизованного логина")
                        error = f"login {login} already exist, take another\n"
                        self.transport.write(error.encode())
                        reactor.callLater(0.5, self.transport.loseConnection)
                        
                        break
                else:
                    self.login = login
                    notification = f"New user: {self.login}"  # формируем уведомление о новом клиенте
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат
                    history = ""
                    if len(self.factory.massages) != 0:
                        for i in range(10):
                            history = history + self.factory.massages[i] + '\n'
                            if i == len(self.factory.massages) - 1:
                                break
                        self.sendLine("Welcome to the chat!\n".encode())
                        self.sendLine(history.encode())
            
            
            else:
                self.sendLine("Invalid login".encode())  # шлем уведомление, если в сообщении ошибка
        
        else:  # если логин уже есть и это следующее сообщение
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента
            
            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)
            self.factory.massages.append(format_message)


class Server(ServerFactory):
    """Класс для управления сервером"""
    
    clients: list  # список клиентов
    protocol = Client  # протокол обработки клиента
    
    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """
        self.massages = []
        self.clients = []  # создаем пустой список клиентов
        
        print("Server started - OK")  # уведомление в консоль сервера
    
    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""
        
        print("Start listening ...")  # уведомление в консоль сервера
    
    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """
        
        data = message.encode()  # закодируем текст в двоичное представление
        
        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )
    
    # запускаем реактор
    reactor.run()
