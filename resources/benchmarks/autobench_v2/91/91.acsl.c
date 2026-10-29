
int main(){

    int x = 0;
    int y = 0;

    /*@
      loop invariant y >= 0;
      loop assigns y;
    */
    while(y >= 0){
        y = y + x;
    }

    //post-condition
    //@ assert( y >= 0);
}
