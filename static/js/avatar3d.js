/* V-SKILL Avatar Studio — local GLB renderer
 * - Loads the project's real /static/models/*.glb files (no CDN)
 * - Lazy loads + caches GLBs
 * - Uses a procedural fallback if WebGL/GLB fails
 * - Main avatar supports drag/touch rotation + wheel/pinch zoom
 * - Mini previews are lightweight and only initialize when visible
 */
(() => {
  'use strict';

  const TAU = Math.PI * 2;
  const SPECIES = {
    fox: [1.00, .47, .24], cat: [.68, .50, 1.00], rabbit: [.88, .72, 1.00],
    panda: [.92, .94, .98], bear: [.62, .38, .20], penguin: [.20, .32, .48]
  };
  const ACCENT = {
    fox: [1.00, .64, .30], cat: [.80, .68, 1.00], rabbit: [1.00, .88, 1.00],
    panda: [1.00, 1.00, 1.00], bear: [.82, .57, .38], penguin: [.34, .52, .72]
  };
  const RARITY = { common: '#aeb9d8', rare: '#55dcff', epic: '#c084fc', legendary: '#ffd166' };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  // ---------- Matrix helpers (column-major, WebGL style) ----------
  const m4 = () => new Float32Array(16);
  function ident(o) { o[0]=1;o[1]=0;o[2]=0;o[3]=0;o[4]=0;o[5]=1;o[6]=0;o[7]=0;o[8]=0;o[9]=0;o[10]=1;o[11]=0;o[12]=0;o[13]=0;o[14]=0;o[15]=1; return o; }
  function mul(a,b) { const o=m4(); for(let c=0;c<4;c++) for(let r=0;r<4;r++) o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3]; return o; }
  function trans(x,y,z) { const o=m4();ident(o);o[12]=x;o[13]=y;o[14]=z;return o; }
  function scale(x,y,z) { const o=m4();ident(o);o[0]=x;o[5]=y;o[10]=z;return o; }
  function rx(a) { const o=m4();ident(o);const c=Math.cos(a),s=Math.sin(a);o[5]=c;o[6]=s;o[9]=-s;o[10]=c;return o; }
  function ry(a) { const o=m4();ident(o);const c=Math.cos(a),s=Math.sin(a);o[0]=c;o[2]=-s;o[8]=s;o[10]=c;return o; }
  function rz(a) { const o=m4();ident(o);const c=Math.cos(a),s=Math.sin(a);o[0]=c;o[1]=s;o[4]=-s;o[5]=c;return o; }
  function perspective(fov,aspect,near,far) { const o=m4(),f=1/Math.tan(fov/2);o[0]=f/aspect;o[5]=f;o[10]=(far+near)/(near-far);o[11]=-1;o[14]=(2*far*near)/(near-far);o[1]=o[2]=o[3]=o[4]=o[6]=o[7]=o[8]=o[9]=o[12]=o[13]=0;o[15]=0;return o; }
  function lookAt(ex,ey,ez,cx,cy,cz) {
    let zx=ex-cx,zy=ey-cy,zz=ez-cz,l=Math.hypot(zx,zy,zz)||1;zx/=l;zy/=l;zz/=l;
    let xx=zz,xy=0,xz=-zx;l=Math.hypot(xx,xy,xz)||1;xx/=l;xz/=l;
    const yx=zy*xz-zz*xy, yy=zz*xx-zx*xz, yz=zx*xy-zy*xx;
    const o=m4();ident(o);o[0]=xx;o[1]=yx;o[2]=zx;o[4]=xy;o[5]=yy;o[6]=zy;o[8]=xz;o[9]=yz;o[10]=zz;
    o[12]=-(xx*ex+xy*ey+xz*ez);o[13]=-(yx*ex+yy*ey+yz*ez);o[14]=-(zx*ex+zy*ey+zz*ez);return o;
  }
  function quat(q) {
    const [x,y,z,w]=q;const x2=x+x,y2=y+y,z2=z+z,xx=x*x2,xy=x*y2,xz=x*z2,yy=y*y2,yz=y*z2,zz=z*z2,wx=w*x2,wy=w*y2,wz=w*z2;
    const o=m4();ident(o);o[0]=1-(yy+zz);o[1]=xy+wz;o[2]=xz-wy;o[4]=xy-wz;o[5]=1-(xx+zz);o[6]=yz+wx;o[8]=xz+wy;o[9]=yz-wx;o[10]=1-(xx+yy);return o;
  }
  function compose(...ms) { let o=m4();ident(o);for(const x of ms)o=mul(o,x);return o; }

  // ---------- Small procedural fallback geometry ----------
  function sphere(lat=14,lon=20) {
    const v=[],n=[],idx=[];
    for(let y=0;y<=lat;y++){const p=y/lat*Math.PI,sp=Math.sin(p),cp=Math.cos(p);for(let x=0;x<=lon;x++){const t=x/lon*TAU,st=Math.sin(t),ct=Math.cos(t);v.push(sp*ct,cp,sp*st);n.push(sp*ct,cp,sp*st);}}
    for(let y=0;y<lat;y++)for(let x=0;x<lon;x++){const a=y*(lon+1)+x,b=a+1,c=a+lon+1,d=c+1;idx.push(a,c,b,b,c,d);}return {v,n,i:idx};
  }
  function box(){
    const p=[[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],[-1,-1,-1],[-1,1,-1],[1,1,-1],[1,-1,-1]],f=[[0,1,2,3,0,0,1],[7,6,5,4,0,0,-1],[3,2,6,5,0,1,0],[0,4,7,1,0,-1,0],[1,7,6,2,1,0,0],[4,0,3,5,-1,0,0]],v=[],n=[],idx=[];let k=0;
    f.forEach(q=>{for(let j=0;j<4;j++){const a=p[q[j]];v.push(...a);n.push(q[4],q[5],q[6]);}idx.push(k,k+1,k+2,k,k+2,k+3);k+=4;});return {v,n,i:idx};
  }
  function torus(R=.72,r=.08,seg=24,tube=8){const v=[],n=[],idx=[];for(let j=0;j<=tube;j++){const q=j/tube*TAU,cq=Math.cos(q),sq=Math.sin(q);for(let i=0;i<=seg;i++){const t=i/seg*TAU,ct=Math.cos(t),st=Math.sin(t);v.push((R+r*cq)*ct,r*sq,(R+r*cq)*st);n.push(cq*ct,sq,cq*st);}}for(let j=0;j<tube;j++)for(let i=0;i<seg;i++){const a=j*(seg+1)+i,b=a+1,c=a+seg+1,d=c+1;idx.push(a,c,b,b,c,d);}return {v,n,i:idx};}
  function cyl(segments=18){const v=[],n=[],idx=[];for(let y=0;y<=1;y++)for(let x=0;x<=segments;x++){const t=x/segments*TAU,ct=Math.cos(t),st=Math.sin(t);v.push(ct,y,st);n.push(ct,0,st);}for(let x=0;x<segments;x++){const a=x,b=x+1,c=segments+1+x,d=c+1;idx.push(a,c,b,b,c,d);}return {v,n,i:idx};}
  function cone(segments=20){const v=[],n=[],idx=[];for(let y=0;y<=1;y++){const r=1-y;for(let x=0;x<=segments;x++){const t=x/segments*TAU,ct=Math.cos(t),st=Math.sin(t);v.push(r*ct,y,r*st);n.push(ct,.7,st);}}for(let x=0;x<segments;x++){const a=x,b=x+1,c=segments+1+x,d=c+1;idx.push(a,c,b,b,c,d);}return {v,n,i:idx};}
  const GEO={sphere:sphere(),box:box(),torus:torus(),cyl:cyl(),cone:cone()};

  function makeDraw(list,geo,color,model,alpha=1){list.push({geo,color,model,alpha});}
  function buildWearables(draws,hat,accessory,badge,t){
    if(hat==='star_hat'){
      makeDraw(draws,GEO.cone,[.40,.45,1],compose(trans(0,1.66,.02),ry(Math.PI/5),scale(.36,.58,.36)));
      makeDraw(draws,GEO.sphere,[1,.82,.15],compose(trans(0,1.97,.02),scale(.12,.12,.12)));
    }
    if(hat==='headphones'){
      makeDraw(draws,GEO.torus,[.78,.83,.90],compose(trans(0,1.02,.02),rz(Math.PI),scale(.72,.72,.72)));
      makeDraw(draws,GEO.box,[.16,.20,.28],compose(trans(-.70,.93,.02),scale(.11,.22,.13)));
      makeDraw(draws,GEO.box,[.16,.20,.28],compose(trans(.70,.93,.02),scale(.11,.22,.13)));
    }
    if(hat==='crown'){
      makeDraw(draws,GEO.cyl,[1,.72,.10],compose(trans(0,1.58,.02),scale(.50,.24,.50)));
      [-.30,0,.30].forEach(x=>makeDraw(draws,GEO.cone,[1,.78,.12],compose(trans(x,1.86,.02),scale(.10,.28,.10))));
    }
    if(accessory==='scarf'){
      makeDraw(draws,GEO.torus,[.75,.28,.70],compose(trans(0,.15,.02),rx(Math.PI/2),scale(.60,.60,.82)));
      makeDraw(draws,GEO.box,[1,.25,.55],compose(trans(.45,-.05,.04),rz(-.18),scale(.10,.30,.07)));
    }
    if(accessory==='backpack'){
      makeDraw(draws,GEO.box,[.15,.28,.48],compose(trans(0,-.05,-.54),scale(.35,.40,.12)));
      makeDraw(draws,GEO.torus,[.28,.35,.48],compose(trans(-.30,.35,.40),rz(Math.PI/2),scale(.44,.44,.44)));
    }
    if(badge==='spark_badge')makeDraw(draws,GEO.cyl,[.20,.82,1],compose(trans(0,.63,.64),rx(Math.PI/2),scale(.14,.05,.14)));
    if(badge==='champion_aura')makeDraw(draws,GEO.torus,[1,.82,.20],compose(trans(0,-1.05,0),rx(Math.PI/2),scale(.95,.95,.95)),.72);
  }
  // ---------- Production procedural fallback / modular Fox ----------
  // This is intentionally a real, readable fox silhouette rather than the old round placeholder.
  function buildFallback(draws,species,hat,accessory,badge,t){
    const fox = species === 'fox';
    const base = SPECIES[species] || SPECIES.fox;
    const accent = ACCENT[species] || ACCENT.fox;

    if(!fox){
      // Keep the other animals compatible with the existing collection.
      makeDraw(draws,GEO.sphere,base,compose(trans(0,0,0),scale(.72,.92,.62)));
      makeDraw(draws,GEO.sphere,base,compose(trans(0,1.18,0),scale(.82,.70,.66)));
      makeDraw(draws,GEO.sphere,[.06,.07,.11],compose(trans(-.28,1.38,.58),scale(.09,.12,.06)));
      makeDraw(draws,GEO.sphere,[.06,.07,.11],compose(trans(.28,1.38,.58),scale(.09,.12,.06)));
      buildWearables(draws,hat,accessory,badge,t); return;
    }

    // Grounded feet + short legs
    makeDraw(draws,GEO.sphere,[.78,.20,.08],compose(trans(-.34,-1.00,.08),scale(.30,.20,.42)));
    makeDraw(draws,GEO.sphere,[.78,.20,.08],compose(trans(.34,-1.00,.08),scale(.30,.20,.42)));
    makeDraw(draws,GEO.sphere,[.93,.30,.07],compose(trans(-.34,-.76,.04),scale(.25,.38,.25)));
    makeDraw(draws,GEO.sphere,[.93,.30,.07],compose(trans(.34,-.76,.04),scale(.25,.38,.25)));

    // Compact body with clear chest
    makeDraw(draws,GEO.sphere,[.93,.28,.07],compose(trans(0,-.12,0),scale(.72,.86,.52)));
    makeDraw(draws,GEO.sphere,[1.0,.96,.88],compose(trans(0,-.08,.47),scale(.38,.58,.13)));

    // Arms + paws
    makeDraw(draws,GEO.sphere,[.93,.28,.07],compose(trans(-.78,-.05,.01),rz(-.16),scale(.24,.62,.24)));
    makeDraw(draws,GEO.sphere,[.93,.28,.07],compose(trans(.78,-.05,.01),rz(.16),scale(.24,.62,.24)));
    makeDraw(draws,GEO.sphere,[1.0,.40,.10],compose(trans(-.84,-.62,.16),scale(.28,.22,.30)));
    makeDraw(draws,GEO.sphere,[1.0,.40,.10],compose(trans(.84,-.62,.16),scale(.28,.22,.30)));

    // Large fox head
    makeDraw(draws,GEO.sphere,[.94,.30,.08],compose(trans(0,.92,.02),scale(.86,.78,.70)));
    makeDraw(draws,GEO.sphere,[1.0,.96,.88],compose(trans(-.34,.69,.53),scale(.42,.30,.16)));
    makeDraw(draws,GEO.sphere,[1.0,.96,.88],compose(trans(.34,.69,.53),scale(.42,.30,.16)));
    makeDraw(draws,GEO.sphere,[1.0,.96,.88],compose(trans(0,.57,.60),scale(.34,.25,.18)));
    makeDraw(draws,GEO.sphere,[.05,.04,.04],compose(trans(0,.56,.77),scale(.10,.07,.08)));

    // Expressive eyes
    for(const x of [-.31,.31]){
      makeDraw(draws,GEO.sphere,[.025,.035,.06],compose(trans(x,.98,.63),scale(.16,.20,.11)));
      makeDraw(draws,GEO.sphere,[1,1,1],compose(trans(x-.035*(x<0?1:-1),1.04,.715),scale(.045,.055,.025)));
    }

    // Upright fox ears: outer cone + smaller inner ear
    for(const x of [-.52,.52]){
      const outer=compose(trans(x,1.62,.00),scale(.34,.58,.30));
      const inner=compose(trans(x,1.66,.24),scale(.19,.34,.10));
      makeDraw(draws,GEO.cone,[.94,.30,.08],outer);
      makeDraw(draws,GEO.cone,[.12,.07,.10],inner);
    }

    // Big fluffy tail behind the body, clearly visible from 3/4 view
    makeDraw(draws,GEO.sphere,[.94,.30,.08],compose(trans(.68,-.18,-.50),rz(-.35),scale(.48,.70,.56)));
    makeDraw(draws,GEO.sphere,[1.0,.40,.10],compose(trans(.98,.30,-.62),rz(-.55),scale(.46,.62,.52)));
    makeDraw(draws,GEO.sphere,[1.0,.96,.88],compose(trans(1.08,.72,-.62),rz(-.70),scale(.36,.44,.42)));

    // Explorer goggles physically attached to the face
    makeDraw(draws,GEO.torus,[.08,.42,.92],compose(trans(-.31,.99,.70),rx(Math.PI/2),scale(.25,.25,.25)));
    makeDraw(draws,GEO.torus,[.08,.42,.92],compose(trans(.31,.99,.70),rx(Math.PI/2),scale(.25,.25,.25)));
    makeDraw(draws,GEO.sphere,[.015,.025,.045],compose(trans(-.31,.99,.73),scale(.20,.16,.035)));
    makeDraw(draws,GEO.sphere,[.015,.025,.045],compose(trans(.31,.99,.73),scale(.20,.16,.035)));
    makeDraw(draws,GEO.box,[.08,.07,.20],compose(trans(0,.99,.71),scale(.45,.12,.10)));
    makeDraw(draws,GEO.torus,[.08,.42,.92],compose(trans(0,.99,.00),rx(Math.PI/2),scale(.73,.73,.73)));

    // Utility belt + two attached pouches
    makeDraw(draws,GEO.torus,[.08,.42,.92],compose(trans(0,-.20,0),rx(Math.PI/2),scale(.70,.70,.70)));
    makeDraw(draws,GEO.box,[.02,.07,.12],compose(trans(-.58,-.28,.39),scale(.30,.24,.18)));
    makeDraw(draws,GEO.box,[.02,.07,.12],compose(trans(.58,-.28,.39),scale(.30,.24,.18)));

    // V-SKILL chest emblem
    makeDraw(draws,GEO.box,[.08,.90,1],compose(trans(-.075,-.05,.62),rz(-.55),scale(.07,.25,.025)));
    makeDraw(draws,GEO.box,[.08,.90,1],compose(trans(.075,-.05,.62),rz(.55),scale(.07,.25,.025)));

    buildWearables(draws,hat,accessory,badge,t);
  }

  // ---------- GLB parser ----------
  const glbCache = new Map();
  function readAccessor(gltf,bin,index){
    const a=gltf.accessors[index], bv=gltf.bufferViews[a.bufferView];
    const comps={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16}[a.type];
    const ctBytes={5121:1,5123:2,5125:4,5126:4}[a.componentType];
    const Ctor={5121:Uint8Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array}[a.componentType];
    if(!comps||!ctBytes||!Ctor)throw new Error('Unsupported accessor');
    const stride=bv.byteStride||comps*ctBytes, start=(bv.byteOffset||0)+(a.byteOffset||0), count=a.count;
    const out=new Array(count*comps);
    if(stride===comps*ctBytes){const view=new Ctor(bin,start,count*comps);for(let i=0;i<view.length;i++)out[i]=view[i];}
    else {const view=new DataView(bin);for(let i=0;i<count;i++)for(let c=0;c<comps;c++){const p=start+i*stride+c*ctBytes;out[i*comps+c]=a.componentType===5126?view.getFloat32(p,true):a.componentType===5125?view.getUint32(p,true):a.componentType===5123?view.getUint16(p,true):view.getUint8(p);}}
    return {data:out,components:comps,count};
  }
  function calcNormals(pos,indices){
    const n=new Float32Array(pos.length);
    for(let k=0;k<indices.length;k+=3){const ia=indices[k]*3,ib=indices[k+1]*3,ic=indices[k+2]*3;
      const ax=pos[ib]-pos[ia],ay=pos[ib+1]-pos[ia+1],az=pos[ib+2]-pos[ia+2];
      const bx=pos[ic]-pos[ia],by=pos[ic+1]-pos[ia+1],bz=pos[ic+2]-pos[ia+2];
      const nx=ay*bz-az*by,ny=az*bx-ax*bz,nz=ax*by-ay*bx;
      n[ia]+=nx;n[ia+1]+=ny;n[ia+2]+=nz;n[ib]+=nx;n[ib+1]+=ny;n[ib+2]+=nz;n[ic]+=nx;n[ic+1]+=ny;n[ic+2]+=nz;
    }
    for(let i=0;i<n.length;i+=3){const l=Math.hypot(n[i],n[i+1],n[i+2])||1;n[i]/=l;n[i+1]/=l;n[i+2]/=l;}return Array.from(n);
  }
  function nodeMatrix(n){
    if(n.matrix)return new Float32Array(n.matrix);
    return compose(trans(...(n.translation||[0,0,0])),quat(n.rotation||[0,0,0,1]),scale(...(n.scale||[1,1,1])));
  }
  function materialColor(gltf,idx){
    const m=gltf.materials?.[idx], c=m?.pbrMetallicRoughness?.baseColorFactor||[.75,.80,.95,1];
    return [c[0],c[1],c[2]];
  }
  function parseGLB(buf){
    const dv=new DataView(buf);if(dv.getUint32(0,true)!==0x46546c67)throw new Error('Invalid GLB header');
    let off=12,json=null,bin=null;
    while(off<buf.byteLength){const len=dv.getUint32(off,true),type=dv.getUint32(off+4,true),data=buf.slice(off+8,off+8+len);off+=8+len;if(type===0x4E4F534A)json=JSON.parse(new TextDecoder().decode(data).replace(/[\u0000\s]+$/,''));else if(type===0x004E4942)bin=data;}
    if(!json||!bin)throw new Error('GLB missing JSON/BIN');
    const draws=[];const scene=json.scenes?.[json.scene??0]||{nodes:[]};
    const walk=(ni,parent)=>{const n=json.nodes?.[ni];if(!n)return;const world=mul(parent,nodeMatrix(n));
      if(n.mesh!=null){const mesh=json.meshes[n.mesh];for(const prim of mesh.primitives||[]){if(prim.mode!=null&&prim.mode!==4)continue;const pa=prim.attributes?.POSITION;if(pa==null||prim.indices==null)continue;const p=readAccessor(json,bin,pa),idx=readAccessor(json,bin,prim.indices);const inds=idx.data.map(Number),norm=prim.attributes.NORMAL!=null?readAccessor(json,bin,prim.attributes.NORMAL).data:calcNormals(p.data,inds);draws.push({geo:{v:p.data,n:norm,i:inds},color:materialColor(json,prim.material),model:world,alpha:(json.materials?.[prim.material]?.pbrMetallicRoughness?.baseColorFactor?.[3]??1)});}}
      for(const c of n.children||[])walk(c,world);
    };
    for(const ni of scene.nodes||[])walk(ni,ident(m4()));
    if(!draws.length)throw new Error('GLB contains no triangle meshes');
    let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(const d of draws)for(let i=0;i<d.geo.v.length;i+=3){const p=d.geo.v.slice(i,i+3);min=p.map((v,j)=>Math.min(min[j],v));max=p.map((v,j)=>Math.max(max[j],v));}
    const center=[(min[0]+max[0])/2,(min[1]+max[1])/2,(min[2]+max[2])/2],size=Math.max(max[0]-min[0],max[1]-min[1],max[2]-min[2])||1;
    return {draws,center,size};
  }
  async function loadGLB(species){
    if(glbCache.has(species))return glbCache.get(species);
    const p=fetch(`/static/models/${encodeURIComponent(species)}.glb?v=20260913-fox3`,{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.arrayBuffer();}).then(parseGLB);
    glbCache.set(species,p);try{return await p;}catch(e){glbCache.delete(species);throw e;}
  }

  function shader(gl,type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s)||'Shader compile failed');return s;}
  function createProgram(gl){
    const vs=shader(gl,gl.VERTEX_SHADER,`attribute vec3 aPos;attribute vec3 aNormal;uniform mat4 uMVP;uniform mat4 uModel;varying vec3 vN;void main(){vN=normalize(mat3(uModel)*aNormal);gl_Position=uMVP*vec4(aPos,1.0);}`);
    const fs=shader(gl,gl.FRAGMENT_SHADER,`precision mediump float;uniform vec3 uColor;uniform float uAlpha;varying vec3 vN;void main(){vec3 N=normalize(vN);vec3 L=normalize(vec3(-.55,.90,.75));float d=max(dot(N,L),0.0);float rim=pow(1.0-max(dot(N,normalize(vec3(0.,0.,1.))),0.0),2.0);vec3 c=uColor*(.28+.82*d)+vec3(.10,.18,.30)*rim;gl_FragColor=vec4(c,uAlpha);}`);
    const p=gl.createProgram();gl.attachShader(p,vs);gl.attachShader(p,fs);gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(p)||'Program link failed');return p;
  }

  function initRenderer(container,config,mini){
    if(container.__vskillRenderer)return container.__vskillRenderer;
    const canvas=document.createElement('canvas');canvas.className='avatar-canvas';container.appendChild(canvas);
    const gl=canvas.getContext('webgl',{antialias:true,alpha:true,preserveDrawingBuffer:false});
    if(!gl){showFallbackMessage(container,'เบราว์เซอร์นี้ไม่รองรับ WebGL');return null;}
    let prog;try{prog=createProgram(gl);}catch(e){console.error('[V-SKILL] WebGL shader error',e);showFallbackMessage(container,'3D Preview unavailable');return null;}
    const loc={pos:gl.getAttribLocation(prog,'aPos'),normal:gl.getAttribLocation(prog,'aNormal'),mvp:gl.getUniformLocation(prog,'uMVP'),model:gl.getUniformLocation(prog,'uModel'),color:gl.getUniformLocation(prog,'uColor'),alpha:gl.getUniformLocation(prog,'uAlpha')};
    gl.useProgram(prog);gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.clearColor(0,0,0,0);
    const state={container,canvas,gl,prog,loc,mini,config:{...config,forceProcedural:!!config.forceProcedural},model:null,failed:false,rot:mini?.10:.08,target:mini?.10:.08,zoom:mini?5.0:4.65,drag:false,lastX:0,lastY:0,start:performance.now(),buffers:new WeakMap(),destroyed:false};
    function resize(){const w=Math.max(1,container.clientWidth),h=Math.max(1,container.clientHeight),d=Math.min(devicePixelRatio||1,2);canvas.width=Math.floor(w*d);canvas.height=Math.floor(h*d);canvas.style.width=w+'px';canvas.style.height=h+'px';gl.viewport(0,0,canvas.width,canvas.height);}
    state.resize=resize;
    const ro=new ResizeObserver(resize);ro.observe(container);resize();
    if(!mini){
      canvas.addEventListener('pointerdown',e=>{state.drag=true;state.lastX=e.clientX;state.lastY=e.clientY;canvas.setPointerCapture?.(e.pointerId);});
      canvas.addEventListener('pointermove',e=>{if(!state.drag)return;state.target+=(e.clientX-state.lastX)*.009;state.lastX=e.clientX;state.lastY=e.clientY;});
      ['pointerup','pointercancel','pointerleave'].forEach(n=>canvas.addEventListener(n,()=>state.drag=false));
      canvas.addEventListener('wheel',e=>{state.zoom=clamp(state.zoom+e.deltaY*.0025,3.5,7.5);e.preventDefault();},{passive:false});
      let pinch=0;canvas.addEventListener('touchstart',e=>{if(e.touches.length===2)pinch=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);},{passive:true});
      canvas.addEventListener('touchmove',e=>{if(e.touches.length!==2||!pinch)return;const n=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);state.zoom=clamp(state.zoom-(n-pinch)*.008,3.5,7.5);pinch=n;},{passive:true});
    }
    container.__vskillRenderer=state;
    container.querySelector('.avatar-3d-loading')?.remove();

    function bufferFor(geo){if(state.buffers.has(geo))return state.buffers.get(geo);const b={};b.v=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b.v);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(geo.v),gl.STATIC_DRAW);b.n=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b.n);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(geo.n),gl.STATIC_DRAW);b.i=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,b.i);const IndexCtor=geo.v.length/3>65535?Uint32Array:Uint16Array;if(IndexCtor===Uint32Array&&!gl.getExtension('OES_element_index_uint'))throw new Error('Large mesh unsupported');gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new IndexCtor(geo.i),gl.STATIC_DRAW);b.count=geo.i.length;b.type=IndexCtor===Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT;state.buffers.set(geo,b);return b;}
    state.render=()=>{
      if(state.destroyed)return;
      const now=performance.now(),t=(now-state.start)/1000;requestAnimationFrame(state.render);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);state.rot+=(state.target-state.rot)*.08;
      const aspect=canvas.width/Math.max(1,canvas.height),proj=perspective(mini?.62:.60,aspect,.1,50),cam=lookAt(0,.18,state.zoom,0,.38,0),viewProj=mul(proj,cam);
      let draws=[];
      if(state.model && !state.config.forceProcedural){const fitScale=(mini?.92:1.12)/state.model.size;const centered=compose(trans(-state.model.center[0],-state.model.center[1],-state.model.center[2]),scale(fitScale,fitScale,fitScale));const base=compose(ry(state.rot),trans(0,.18+Math.sin(t*1.35)*.025,0),centered);draws=state.model.draws.map(d=>({...d,model:mul(base,d.model)}));const wearables=[];buildWearables(wearables,state.config.hat,state.config.accessory,state.config.badge,t);wearables.forEach(d=>d.model=mul(base,d.model));draws.push(...wearables);}
      else {buildFallback(draws,state.config.species,state.config.hat,state.config.accessory,state.config.badge,t);const base=compose(ry(state.rot),trans(0,-.05+Math.sin(t*1.35)*.035,0),scale(mini?.95:1.12,mini?.95:1.12,mini?.95:1.12));draws.forEach(d=>d.model=mul(base,d.model));}
      gl.useProgram(prog);
      for(const d of draws){const b=bufferFor(d.geo),mvp=mul(viewProj,d.model);gl.bindBuffer(gl.ARRAY_BUFFER,b.v);gl.enableVertexAttribArray(loc.pos);gl.vertexAttribPointer(loc.pos,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,b.n);gl.enableVertexAttribArray(loc.normal);gl.vertexAttribPointer(loc.normal,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,b.i);gl.uniformMatrix4fv(loc.mvp,false,mvp);gl.uniformMatrix4fv(loc.model,false,d.model);gl.uniform3fv(loc.color,d.color);gl.uniform1f(loc.alpha,d.alpha??1);gl.drawElements(gl.TRIANGLES,b.count,b.type,0);}
    };
    state.render();
    // Load the real GLB asynchronously. Fallback stays visible until it succeeds.
    if(!state.config.forceProcedural){loadGLB(state.config.species).then(model=>{if(state.destroyed)return;state.model=model;container.classList.add('glb-ready');}).catch(err=>{state.failed=true;container.classList.add('glb-fallback');console.warn(`[V-SKILL] ${state.config.species}.glb unavailable — using modular fallback`,err);});}
    return state;
  }

  function showFallbackMessage(container,text,subtle=false){let el=container.querySelector('.avatar-3d-status');if(!el){el=document.createElement('div');el.className='avatar-3d-status';container.appendChild(el);}el.textContent=text;el.dataset.subtle=subtle?'1':'0';}
  function cfg(el){return {species:el.dataset.species||'fox',hat:el.dataset.hat||'',accessory:el.dataset.accessory||'',badge:el.dataset.badge||'',forceProcedural:el.dataset.forceProcedural==='1'};}
  function ensureRenderer(el,mini=false){return initRenderer(el,cfg(el),mini);}

  // Lazy mini previews: cards below the fold do not immediately cost GPU/CPU.
  const minis=[...document.querySelectorAll('.avatar-mini-3d')];
  if('IntersectionObserver' in window){const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){ensureRenderer(e.target,true);io.unobserve(e.target);}}),{rootMargin:'160px'});minis.forEach(el=>io.observe(el));}
  else minis.forEach(el=>ensureRenderer(el,true));

  const main=document.getElementById('avatar3d-main');if(main)ensureRenderer(main,false);

  // ---------- Selection / equip UI ----------
  function statePayload(data){
    const av=data.avatar||data;
    return {
      species:av.species||'fox',
      hat:av.hat||av.equipped_hat_asset||'',
      accessory:av.accessory||av.equipped_accessory_asset||'',
      badge:av.badge||av.equipped_badge_asset||'',
      ids:data.equipped||{}
    };
  }
  function applyMain(payload){
    if(!main)return;const r=main.__vskillRenderer;if(!r)return;
    const next=statePayload(payload);r.config.species=next.species;r.config.hat=next.hat;r.config.accessory=next.accessory;r.config.badge=next.badge;r.config.forceProcedural=true;r.model=null;r.failed=false;r.start=performance.now();main.querySelector('.avatar-3d-status')?.remove();
    loadGLB(next.species).then(m=>{r.model=m;main.classList.add('glb-ready');}).catch(e=>{r.failed=true;main.classList.add('glb-fallback');console.warn('[V-SKILL] selected GLB failed',e);});
  }
  function refreshMiniSpecies(species){
    document.querySelectorAll('.avatar-mini-3d').forEach(el=>{
      if(el.closest('.wardrobe-item-v4')?.dataset.slot==='species')return;
      const r=el.__vskillRenderer;if(r){r.config.species=species;r.model=null;loadGLB(species).then(m=>{r.model=m;});}
      else el.dataset.species=species;
    });
  }
  function updateCards(payload){
    const next=statePayload(payload),ids=next.ids||{};
    document.querySelectorAll('.wardrobe-item-v4').forEach(card=>{
      const btn=card.querySelector('form button'),form=card.querySelector('form'),id=form?.querySelector('input[name=item_id]')?.value,slot=card.dataset.slot;
      let selected=false;
      if(slot==='species')selected=card.querySelector('.avatar-mini-3d')?.dataset.previewItem===next.species;
      if(slot==='hat')selected=String(id)===String(ids.hat||'');
      if(slot==='accessory')selected=String(id)===String(ids.accessory||'');
      if(slot==='badge')selected=String(id)===String(ids.badge||'');
      card.classList.toggle('equipped',selected);
      if(btn){btn.classList.toggle('equipped-btn',selected);btn.classList.toggle('secondary',!selected);if(selected)btn.textContent='✓ กำลังสวมใส่';else btn.textContent=slot==='species'?'เลือกเป็นคู่หู':'สวมใส่ไอเทม';}
    });
    refreshMiniSpecies(next.species);
  }

  document.querySelectorAll('.wardrobe-item-v4 form').forEach(form=>form.addEventListener('submit',async e=>{
    e.preventDefault();const btn=form.querySelector('button');if(!btn)return;btn.disabled=true;btn.dataset.old=btn.textContent;btn.textContent='กำลังบันทึก…';
    try{const res=await fetch(window.location.pathname,{method:'POST',body:new FormData(form),headers:{'Accept':'application/json','X-Requested-With':'XMLHttpRequest'}});if(!res.ok)throw new Error(`HTTP ${res.status}`);const data=await res.json();applyMain(data);updateCards(data);window.dispatchEvent(new CustomEvent('vskill:avatar-updated',{detail:data}));}
    catch(err){console.error('[V-SKILL] avatar update failed',err);btn.textContent='ลองอีกครั้ง';setTimeout(()=>{btn.textContent=btn.dataset.old||'สวมใส่ไอเทม';},1200);}
    finally{btn.disabled=false;}
  }));

  window.VSkillAvatar={refresh:(payload)=>{applyMain(payload);updateCards(payload);},loadGLB};
})();
