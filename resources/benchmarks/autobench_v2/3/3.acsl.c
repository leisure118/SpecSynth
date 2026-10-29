
void foo(int y, int z)
{
   int x = 0;

   /*@
     loop invariant 0 <= x <= 5;
     loop invariant z >= y || x == 0;
     loop assigns x, y;
     loop variant 5 - x;
   */
   while(x < 5) {
      x += 1;
      if( z <= y) {
         y = z;
      }
   }

   //post-condition
   //@ assert(z >= y);
}
