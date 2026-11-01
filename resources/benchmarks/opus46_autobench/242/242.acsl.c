// jm2006_variant_true-unreach-call.c
int main() {
    int i;
    int j;

    int x = i;
    int y = j;
    int z = 0;
    
    /*@
      loop invariant x + z == i;
      loop invariant y + 2*z == j;
      loop invariant z >= 0;
      loop assigns x, y, z;
    */
    while (x != 0) {
    	x--;
    	y -= 2;
    	z++;
    }

    if (i == j) {
    	//@ assert(y == -z);
    }
    
    return 0;
}
