void max_ptr(int* a, int* b){
    if(*a < *b){
        int tmp = *b;
        *b = *a;
        *a = tmp;
    }
}
int main(){
    int x = 10, y = 20;
    max_ptr(&x, &y);
    //@ assert x == 20 && y == 10;
    return 0;
}