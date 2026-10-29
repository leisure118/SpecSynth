void order_3(int* a, int* b, int* c){
    if(*a > *b){
        int tmp = *b;
        *b = *a;
        *a = tmp;
    }
    if(*a > *c){
        int tmp = *c;
        *c = *a;
        *a = tmp;
    }
    if(*b > *c){
        int tmp = *b;
        *b = *c;
        *c = tmp;
    }
}
int main(){
    int x = 10, y = 20, z = 15;
    order_3(&x, &y, &z);
    //@ assert x == 10 && y == 15 && z == 20;
    return 0;
}