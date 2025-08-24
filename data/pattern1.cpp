void pattern1_lower_triangle(int n) {
    int count = 0;

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < i; j++) {  // j < i - строгое неравенство
            // Обработка элементов ниже главной диагонали
            count++;
            // lower_matrix[i][j] = compute_value(i, j);
        }
    }
}