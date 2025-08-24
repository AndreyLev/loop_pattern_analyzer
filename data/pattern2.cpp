void pattern2_upper_triangle(int n) {
    int count = 0;

    for (int i = 0; i < n; i++) {
        for (int j = i; j < n; j++) {  // j >= i - включая диагональ
            // Обработка элементов на и выше главной диагонали
            count++;
            // upper_matrix[i][j] = compute_value(i, j);
        }
    }
}