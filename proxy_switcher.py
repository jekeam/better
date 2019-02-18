class ProxySwitcher:
    def __init__(self, size: int, proxies: list) -> None:
        self.size = size
        self.proxies = proxies
        self.cur_num = 0
        if len(self.proxies) != (self.size):
            raise ValueError('__init__: wrong size')
        if not isinstance(proxies, (list,)):
            raise ValueError('__init__: wrong type')

    def get_cur_proxy(self) -> str:
        return str(self.proxies[self.cur_num])

    def get_next_proxy(self) -> str:
        # flick
        self.cur_num = self.cur_num + 1
        if self.cur_num >= self.size:
            self.cur_num = 0
        proxy = str(self.proxies[self.cur_num])
        return proxy

    def rep_cur_proxy(self, proxy: str) -> None:
        if not isinstance(proxy, (str,)):
            raise ValueError('rep_cur_proxy: wrong type')
        self.proxies[self.cur_num] = proxy


if __name__ == "__main__":
    PS = ProxySwitcher(3, ['1', '2', '3'])
    print('c: ' + PS.get_cur_proxy())
    print('n: ' + PS.get_next_proxy())
    print('n: ' + PS.get_next_proxy())

    print('n: ' + PS.get_next_proxy())
    print('n: ' + PS.get_next_proxy())
    print('n: ' + PS.get_next_proxy())
    PS.rep_cur_proxy('xxx')
    print('n: ' + PS.get_next_proxy())
    print('n: ' + PS.get_next_proxy())
    print('n: ' + PS.get_next_proxy())
