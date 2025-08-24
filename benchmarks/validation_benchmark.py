# benchmark для валидации формул
import random

class DirectCount:
    @staticmethod
    def pattern_1(n: int):
        count = 0
        for i in range(n):
            for j in range(i):
                count += 1
        return count

    @staticmethod
    def pattern_2(n: int):
        count = 0
        for i in range(n):
            for j in range(i,n):
                count += 1
        return count

    @staticmethod
    def pattern_3(n: int, k: int):
        count = 0
        T = n
        for t in range(T):
            for i in range(max(0, t-k), min(n, t+k+1)):
                count = count + 1
        return count

    @staticmethod
    def pattern_4(n: int, m: int):
        count = 0
        for diag in range(n + m - 1):
            for i in range(max(0, diag-m+1), min(diag+1, n)):
                count = count + 1
        return count

    @staticmethod
    def pattern_5(n: int, k: int):
        count = 0
        for i in range(n):
            for j in range(max(0, i-k), min(n, i+k+1)):
                count = count + 1
        return count

    @staticmethod
    def pattern_6(n: int, b: int):
        count = 0
        for i in range(n):
            for j in range(max(0, i-b), min(n, i+b+1)):
                count = count + 1
        return count


class Formulas:
    @staticmethod
    def pattern_1(n: int):
        return n*(n-1)/2

    @staticmethod
    def pattern_2(n: int):
        return n*(n+1)/2

    @staticmethod
    def pattern_3(n: int, k: int):
        return n*(2*k+1)-k*(k+1)

    @staticmethod
    def pattern_4(n: int, m: int):
        return n*m

    @staticmethod
    def pattern_5(n: int, k: int):
        return n * (2 * k + 1) - k * (k + 1)

    @staticmethod
    def pattern_6(n: int, b: int):
        return n * (2 * b + 1) - b * (b + 1)

class Benchmark:
    @staticmethod
    def run():
        res = dict()
        for p in range(6):
            res[p] = 0

        samples = 33
        for i in range(samples):
            n = random.randint(1,100)
            m = n + random.randint(1, 100)

            #паттерн 1
            c1 = Formulas.pattern_1(n)
            c2 = DirectCount.pattern_1(n)
            if c1 == c2:
                res[0] = res[0] + 1

            #паттерн 2
            c1 = Formulas.pattern_2(n)
            c2 = DirectCount.pattern_2(n)
            if c1 == c2:
                res[1] = res[1] + 1

            #паттерн 3
            k = random.randint(1, n)
            c1 = Formulas.pattern_3(n, k)
            c2 = DirectCount.pattern_3(n, k)
            if c1 == c2:
                res[2] = res[2] + 1

            #паттерн 4
            c1 = Formulas.pattern_4(n, m)
            c2 = DirectCount.pattern_4(n, m)
            if c1 == c2:
                res[3] = res[3] + 1

            #паттерн 5
            k = random.randint(1, n)
            c1 = Formulas.pattern_5(n, k)
            c2 = DirectCount.pattern_5(n, k)
            if c1 == c2:
                res[4] = res[4] + 1

            #паттерн 6
            b = random.randint(1, n)
            c1 = Formulas.pattern_6(n, b)
            c2 = DirectCount.pattern_6(n, b)
            if c1 == c2:
                res[5] = res[5] + 1

        for p in range(6):
            res[p] = res[p] / samples

        print(res)

Benchmark.run()