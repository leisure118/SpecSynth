/*@
  requires \valid(a) && \valid(b) && \valid(c);
  assigns *a, *b, *c;
  ensures *a <= *b <= *c &&
          \old(*a) + \old(*b) + \old(*c) == *a + *b + *c &&
          \old(*a) * \old(*a) + \old(*b) * \old(*b) + \old(*c) * \old(*c) ==
          *a * *a + *b * *b + *c * *c &&
          (*a == \old(*a) || *a == \old(*b) || *a == \old(*c)) &&
          (*b == \old(*a) || *b == \old(*b) || *b == \old(*c)) &&
          (*c == \old(*a) || *c == \old(*b) || *c == \old(*c));
*/
void order_3(int* a, int* b, int* c){
    if(*a > *b){
        int tmp = *b;
        *b = *a;
        *a = tmp;
    }
    //@ assert *a <= *b;
    if(*a > *c){
        int tmp = *c;
        *c = *a;
        *a = tmp;
    }
    //@ assert *a <= *b && *a <= *c;
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