from multiprocessing import Process, Queue
import time
from random import randint

#
#
# def f1(s, q):
#     r = randint(1, 5)
#     print(s, str(r))
#     time.sleep(r)
#
#
# def f2(s, q):
#     r = randint(1, 5)
#     print(s, str(r))
#     time.sleep(r)
#
#
# if __name__ == '__main__':
#     q = Queue()
#     p = Process(target=f1, args=('fonbet', q,))
#     p2 = Process(target=f2, args=('olimp', q,))
#
#     p.start()
#     p2.start()
#
#     p.join()
#     p2.join()
sentinel = -1


def creator(data, q):
    """
    Creates data to be consumed and waits for the consumer
    to finish processing
    """
    print('Creating data and putting it on the queue')
    for item in data:
        r = randint(1, 5)
        print('sleep', str(r), 'data:', str(item))
        time.sleep(r)
        q.put(item)


def my_consumer(q):
    """
    Consumes some data and works on it
    In this case, all it does is double the input
    """
    while True:
        data = q.get()
        print('data found to be processed: {}'.format(data))

        if data is sentinel:
            break


if __name__ == '__main__':
    q = Queue()
    data = [5, 10, 13, -1]

    process_one = Process(target=creator, args=(data, q))
    process_two = Process(target=my_consumer, args=(q,))

    process_one.start()
    process_two.start()

    q.close()
    q.join_thread()

    process_one.join()
    process_two.join()
