/*@
  requires \valid(a) && \valid(b);
  assigns *a, *b;
  ensures *a >= *b;
  ensures (\old(*a) < \old(*b)) ==> (*a == \old(*b) && *b == \old(*a));
  ensures (\old(*a) >= \old(*b)) ==> (*a == \old(*a) && *b == \old(*b));
*/
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