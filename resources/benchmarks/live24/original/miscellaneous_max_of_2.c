int max(int x, int y) {
    if (x >= y) {
        return x;
    }
    return y;
}
int main() {
    int a = 5;
    int b = 10;
    int result = max(a, b);
    //@ assert result == 10;
    return 0;
}