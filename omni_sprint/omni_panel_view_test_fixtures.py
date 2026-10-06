"""SDK widget boundary for the real Omni Sprint view tests."""


class Struct:
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        value = Struct()
        setattr(self, name, value)
        return value


class Enum:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, member):
        return f'{self.name}.{member}'


class Widget:
    created = []

    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner
        self.children, self.slots, self.calls = [], [], {}
        self.checked = self.selecting = False
        self.value = 0.0
        self.Font = Struct()
        self.created.append(self)

    def __getattr__(self, name):
        if name.startswith('Set') or name.startswith('AddChild'):
            return lambda *args: self.call(name, args)
        if name[:1].isupper():
            value = Struct()
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def call(self, name, args):
        if name == 'SetContent':
            self.children[:] = [args[0]]
        elif name.startswith('AddChild'):
            self.children.append(args[0])
            slot = Widget('Slot', self)
            self.slots.append(slot)
            return slot
        self.calls[name] = args

    def IsChecked(self):
        return self.checked

    def GetValue(self):
        return self.value

    def GetIsSelectingKey(self):
        return self.selecting
