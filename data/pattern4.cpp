void pattern4_diagonal_iteration(int n, int m) {
    int count = 0;

    // Обход по диагоналям (сумма координат постоянна)
    for (int diag = 0; diag < n + m - 1; diag++) {
        int start_i = max(0, diag - m + 1);
        int end_i = min(diag + 1, n);

        for (int i = start_i; i < end_i; i++) {
            int j = diag - i;
            count++;
        }
    }

}
