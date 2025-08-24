void pattern8_parallelogram_shift(int n, int k) {
    int count = 0;

    for (int i = 0; i < n; i++) {
        // Для каждой строки i ограничиваем j радиусом k
        int start_j = max(0, i - k);
        int end_j = min(n, i + k + 1);

        for (int j = start_j; j < end_j; j++) {
            // Обработка в полосе шириной 2k+1 вокруг диагонали
            count++;
            // process_local_interaction(i, j);
        }
    }

}