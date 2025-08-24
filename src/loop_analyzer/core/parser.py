import  clang.cindex as clang

class ClangLoopParser:
    def __init__(self):
        try:
            clang.conf.set_library_file('/usr/lib/x86_64-linux-gnu/libclang-10.so.1')
        except:
            try:
                clang.conf.set_library_file('/usr/local/lib/libclang.so')
            except:
                print("Предупреждение: libclang может быть не найдена. Убедитесь, что Clang установлен.")

        self.index = clang.Index.create()

        self._parse_cache = {}

c = ClangLoopParser()