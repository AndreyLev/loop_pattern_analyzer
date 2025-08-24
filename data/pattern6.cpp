void pattern9_band_matrix(int n, int bandwidth) {
    int count = 0;

    for (int i = 0; i < n; i++) {
        // Обрабатываем только элементы в полосе |i-j| <= bandwidth
        int start_j = max(0, i - bandwidth);
        int end_j = min(n, i + bandwidth + 1);

        for (int j = start_j; j < end_j; j++) {
            // Обработка только ненулевых элементов ленточной матрицы
            count++;
            // band_matrix[i][j] = compute_band_value(i, j);
        }
    }

    int formula_result = n * (2*bandwidth + 1) - bandwidth * (bandwidth + 1);
}