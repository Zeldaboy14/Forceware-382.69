/* GP108 diagnostic fan protocol: XP786150/210/785ED0 -> native451A00/451D5C.
 * Uses original XP objects, native type1/type2 device callbacks and type1 controller callbacks, and bounded synchronous transport.
 * All table bytes regenerated in zeroed pool, never copied from old stack tail.
 * Old stack reserves 16 entries although accessor strides support32; allocate
 * native32 entries. Class1 widens base header fields within unchanged96 stride.
 * Newly introduced channel selector is FF (absent in XP, matches this board).
 * Device type2 retains the existing 64-byte wire record; controller types other
 * than1 remain unsupported. No change to channel selection or transport.
 */
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
#define S __attribute__((stdcall))
#define D(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define W(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define B(p,o) (*(u8 *)((u8 *)(p)+(o)))
typedef u32(S *ser)(void*,void*,void*);
typedef u32(S *timer)(void*,u32,void*,u32);
typedef u32(S *transport)(void*,void*,void*,void*,void*,u32,void*,void*,void*,void*);
extern void *S gp108_fan_allocate(u32);
extern void S gp108_fan_free(void*);
extern u32 S gp108_fan_transport(void*,void*,void*,void*,void*,u32,void*,void*,void*,void*);
static void zero(void *p,u32 n){u32 i;for(i=0;i<n;i++)B(p,i)=0;}
u32 S gp108_fan_serialize(void *gpu,void *fan,u32 alternate,u32 cls,void *out)
{
 void *g;u32 i,mask,*objs,st,stride=cls?96:64,size=16+32*stride;
 if(!gpu||!fan||!out||alternate>1||cls>1||D(gpu,0x1638)!=(u32)fan)return 0x1f;
 g=(u8*)fan+(cls?0x11f8:0xfbc)+(alternate?0x11c:0);
 mask=D(g,0);objs=(u32*)D(g,8);
 if(!objs||B(g,0x10)!=32||!D(g,0x58))return 0x1f;
 for(i=0;i<32;i++)if(mask&(1u<<i)){
  void *o=(void*)objs[i];
  if(!o||!D(o,0x10))return 0x1f;
  /* Native XP and matched382.23 both serialize device type2 at stride64. */
  if(cls ? B(o,0)!=1 : (B(o,0)!=1 && B(o,0)!=2))return 0x1f;
  /* Existing curve serializer divides by each segment's width. */
  if(cls&&(D(o,0x5c)==D(o,0x50)||D(o,0x68)==D(o,0x5c)))return 0x1f;
 }
 zero(out,size);st=((ser)D(g,0x58))(gpu,g,out);if(st)return st;
 for(i=0;i<32;i++)if(cls&&(mask&(1u<<i))){
  u8 *e=(u8*)out+16+stride*i;u16 period=W(e,2);u8 control=e[4];
  e[2]=255;e[3]=0;W(e,4)=period;e[6]=control;e[7]=0;
 }
 return 0;
}
