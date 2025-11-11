class node:
    def __init__(self, data):
        self.data = data
        self.next = None

class stack:
    def __init__(self):
        self.head = None
        self.size = 0

    def push(self, item):
        new_node = node(item)
        new_node.next = self.head
        self.head = new_node
        self.size += 1

    def pop(self):
        if self.isEmpty():
            return "Belum ada riwayat bacaan"
        deleted = self.head
        self.head = self.head.next
        self.size -= 1
        return deleted.data

    def peek(self):
        if self.isEmpty():
            return "Anda belum membaca 1 chapter pun"
        return self.head.data

    def sizeStack(self):
        return self.size

    def isEmpty(self):
        return self.size == 0