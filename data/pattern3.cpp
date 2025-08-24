void pattern6_trapezoid(int T, int n, int k) {
    int count = 0;

    for (int t = 0; t < T; t++) {
        // Границы зависят от времени t и радиуса k
        int start = max(0, t - k);
        int end = min(n, t + k + 1);

        for (int i = start; i < end; i++) {
            // Обработка в пределах "волны" радиусом k
            count++;
            // stencil_operation(t, i);
        }
    }
}