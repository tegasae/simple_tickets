from abc import ABC, abstractmethod


class UserService(ABC):
    @abstractmethod
    def user_valid(self,username:str,password:str)->bool:
        raise NotImplementedError
