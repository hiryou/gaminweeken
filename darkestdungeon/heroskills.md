Example graph

Darkest dungeon heroes & skills mapping:

```mermaid
%%{ init: {
    'flowchart': {'nodeSpacing': 120, 'rankSpacing': 45, 'curve': 'basis'}, 
    'theme': 'dark', 'themeVariables': { 
        'fontSize': '42px'
    },
    "themeCSS": ".edge-thickness-normal {stroke-width: 14px !important;} .edgeLabel {line-height: 1.0 !important;}"
} }%%

graph TB

    %% css default nodes %%
    classDef default stroke:#151517,fill:none;

    classDef nodeSkillPlain stroke:#fff,fill:#fff,color:#000;

    classDef nodeHeal stroke:#2c3291,fill:#2c3291;
    classDef nodeHealSml stroke:#fff,stroke-width:14px,fill:#2c3291,stroke-dasharray: 1 10;
    classDef nodeHealSelf stroke:#5343e8,fill:#5343e8;
    
    classDef nodeHeroTitle stroke:#151517,fill:none,stroke-width:4px;
    classDef nodeHeroTeam stroke:#151517,fill:#8817ad,stroke-width:16px;
    classDef nodeHeroPlain stroke:#151517,fill:grey,stroke-width:4px;
    classDef nodeHeroArmorPierce stroke:#ba583a,fill:#ba583a;
    
    classDef sgraphHeroPlain color:#2c3291,fill:grey,rx:50,ry:50;
    classDef sgraphHeroHeal stroke:#2c3291,fill:#2c3291,color:#2c3291,rx:50,ry:50;
    classDef sgraphHeroHealSml stroke:#fff,stroke-width:14px,fill:#2c3291,color:#2c3291,stroke-dasharray: 5 20,rx:50,ry:50;
    classDef sgraphHeroHealBleed stroke:#520b11,stroke-width:28px,fill:#2c3291,color:#2c3291,stroke-dasharray: 5 15,rx:50,ry:50;
    classDef sgraphHeroHealSelf fill:#5343e8,color:#5343e8,rx:50,ry:50;
    classDef sgraphHeroArmorPierce stroke:#ba583a,fill:#ba583a,color:#2c3291,rx:50,ry:50;
    classDef sgraphHeroFinale stroke:#b03c3c,fill:#b03c3c,color:#2c3291,rx:50,ry:50;
    
    classDef nodeBuff stroke:#8817ad,fill:#8817ad;
    classDef nodeSelfBuff stroke:#8817ad,fill:#504d54,stroke-width:4px;
    classDef edgeBuff stroke:#8817ad,color:#8817ad;
    
    classDef nodeShuffle stroke:#292e2c,fill:#292e2c;
    classDef edgeShuffle stroke:#292e2c,color:#292e2c;
    
    classDef nodeCure stroke:#2c3291,fill:#2c3291;
    classDef edgeCure stroke:#2c3291,color:#2c3291;
    
    classDef nodeGuard stroke:#2a6f7d,fill:#2a6f7d;
    classDef edgeGuard stroke:#2a6f7d,color:#2a6f7d;
    
    classDef nodeStun stroke:#ad9d3e,fill:#ad9d3e;
    classDef edgeStun stroke:#ad9d3e,color:#ad9d3e;
    
    classDef nodeMark stroke:#9c4f4f,fill:#9c4f4f;
    classDef edgeMark stroke:#9c4f4f,color:#9c4f4f;
    
    classDef nodePull stroke:#8468ad,fill:#8468ad;
    classDef edgePull stroke:#8468ad,color:#8468ad;
    
    classDef nodeBlight stroke:#569c68,fill:#569c68;
    classDef edgeBlight stroke:#569c68,color:#569c68;
    
    classDef nodeDebuff stroke:#000,fill:#000,color:#fff;
    classDef edgeDebuff stroke:#000,color:#000;
    
    classDef nodeBleed stroke:#520b11,fill:#520b11;
    classDef edgeBleed stroke:#520b11,color:#520b11;
    
    
    subgraph _heroes_skills_[Heroes->Skills]
        direction LR
        
        %% declare common actions here
        guard[guard]
        cure[cure:<br>blight,bled]
        riposte[riposte]
        
        %% css styling skill nodes %%
        class guard nodeGuard;
        class riposte nodeSkillPlain;
        class heal nodeHeal;
        class cure nodeCure;
        
        %% below, each hero is a subgraph w/ hero title, buff & debuff line items
        
        subgraph sgraph_Abomination[ ]
            direction TB
            
            hero_Abomination([Abomination<br>#9876;#9876; #8982;#8982;])
            Abomination_buff@{ shape: procs, label: "(SELF)<br>+spd,dmg<br>-stress<br>+dmg"}
            Abomination_debuff@{ shape: procs, label: "-dod,<br>-spd"}
            hero_Abomination ---> Abomination_buff & Abomination_debuff
        
            class hero_Abomination nodeHeroTitle;
            class Abomination_buff nodeSelfBuff;
            class Abomination_debuff nodeDebuff;
        end
        
        subgraph sgraph_Doctor[ ]
            direction TB
            
            hero_Doctor(PlagueDoctor<br>#9876; #8982;#8982;#8982;<br><u>heal</u>: sml)
            Doctor_buff@{ shape: procs, label: "+dmg,spd"}
            Doctor_debuff@{ shape: procs, label: " "}
            hero_Doctor ---> Doctor_buff & Doctor_debuff
        
            class hero_Doctor nodeHeroTitle;
            class Doctor_buff nodeBuff;
            class Doctor_debuff nodeDebuff;
        end
        
        subgraph sgraph_Occultist[ ]
            direction TB
            
            hero_Occultist(Occultist<br>#9876; #8982;#8982;#8982;<br><u>heal</u>: ?++)
            Occultist_buff@{ shape: procs, label: " "}
            Occultist_debuff@{ shape: procs, label: "-dmg,prot"}
            hero_Occultist ---> Occultist_buff & Occultist_debuff
        
            class hero_Occultist nodeHeroTitle;
            class Occultist_buff nodeBuff;
            class Occultist_debuff nodeDebuff;
        end
        
        subgraph sgraph_BountyHunter[ ]
            direction TB
            
            hero_BountyHunter([#9022; #9022; #9022; <br>BountyHunter<br>#9876;#9876; #8982;#8982;])
            BountyHunter_buff@{ shape: procs, label: "(SELF)<br>+spd"}
            BountyHunter_debuff@{ shape: procs, label: "-prot<br>+dmg,-spd"}
            hero_BountyHunter ---> BountyHunter_buff & BountyHunter_debuff
        
            class hero_BountyHunter nodeHeroTitle;
            class BountyHunter_buff nodeSelfBuff;
            class BountyHunter_debuff nodeDebuff;
        end
        
        subgraph sgraph_GraveRobber[ ]
            direction TB
            
            hero_GraveRobber([#9022; #9022; #9022; <br>GraveRobber<br>#9876;#9876; #8982;#8982;])
            GraveRobber_buff@{ shape: procs, label: "(SELF)<br>+stealth<br>+dod,spd"}
            GraveRobber_debuff@{ shape: procs, label: " "}
            hero_GraveRobber ---> GraveRobber_buff & GraveRobber_debuff
        
            class hero_GraveRobber nodeHeroTitle;
            class GraveRobber_buff nodeSelfBuff;
            class GraveRobber_debuff nodeDebuff;
        end
        
        subgraph sgraph_HoundMaster[ ]
            direction TB
            
            hero_HoundMaster@{ shape: docs, label: "#9022; #9022; <br>HoundMaster<br>#9876; #8982;#8982;#8982;"}
            HoundMaster_buff@{ shape: procs, label: "++dod<br>---stress"}
            HoundMaster_debuff@{ shape: procs, label: "-prot"}
            hero_HoundMaster ---> HoundMaster_buff & HoundMaster_debuff
        
            class hero_HoundMaster nodeHeroTeam;
            class HoundMaster_buff nodeBuff;
            class HoundMaster_debuff nodeDebuff;
        end
        
        subgraph sgraph_Arbalest[ ]
            direction TB
            
            hero_Arbalest(#9022; #9022; <br>Arbalest/Musketeer<br>#8982;#8982;#8982;#8982;<br><u>heal</u>: +)
            Arbalest_buff@{ shape: procs, label: "+spd<br>--stunned<br>--marked"}
            Arbalest_debuff@{ shape: procs, label: "-acc,crit<br>-dod<br>-stealth"}
            hero_Arbalest ---> Arbalest_buff & Arbalest_debuff
        
            class hero_Arbalest nodeHeroTitle;
            class Arbalest_buff nodeBuff;
            class Arbalest_debuff nodeDebuff;
        end
        
        %% subgraph sgraph_Musketeer[ ]
        %%     direction TB
            
        %%     hero_Musketeer(#9022; #9022; <br>Musketeer<br>#8982;#8982;#8982;#8982;<br><u>heal</u>: +)
        %%     Musketeer_buff@{ shape: procs, label: "+spd(self)<br>--stunned<br>--marked"}
        %%     Musketeer_debuff@{ shape: procs, label: "-acc,crit<br>-dod"}
        %%     hero_Musketeer ---> Musketeer_buff & Musketeer_debuff
        
        %%     class hero_Musketeer nodeHeroTitle;
        %%     class Musketeer_buff nodeBuff;
        %%     class Musketeer_debuff nodeDebuff;
        %% end
        
        subgraph sgraph_Antiquarian[ ]
            direction TB
            
            hero_Antiquarian@{ shape: docs, label: "Antiquarian<br>#9876; #8982;#8982;<br><u>heal</u>: sml"}
            Antiquarian_buff@{ shape: procs, label: "+++dod<br>++prot"}
            Antiquarian_debuff@{ shape: procs, label: "-acc"}
            hero_Antiquarian ---> Antiquarian_buff & Antiquarian_debuff
        
            class hero_Antiquarian nodeHeroTeam;
            class Antiquarian_buff nodeBuff;
            class Antiquarian_debuff nodeDebuff;
        end
        
        subgraph sgraph_Vestal[ ]
            direction TB
            
            hero_Vestal(Vestal<br>#9876; #8982;#8982;#8982;<br><u>heal</u>: ++)
            Vestal_buff@{ shape: procs, label: " "}
            Vestal_debuff@{ shape: procs, label: "-stealth<br>-dod"}
            hero_Vestal ---> Vestal_buff & Vestal_debuff
        
            class hero_Vestal nodeHeroTitle;
            class Vestal_buff nodeBuff;
            class Vestal_debuff nodeDebuff;
        end
        
        subgraph sgraph_Crusader[ ]
            direction TB
            
            hero_Crusader(Crusader<br>#9876;#9876;#9876; #8982;<br><u>heal</u>: +)
            Crusader_buff@{ shape: procs, label: "+prot(self)<br>-stress"}
            Crusader_debuff@{ shape: procs, label: " "}
            hero_Crusader ---> Crusader_buff & Crusader_debuff
        
            class hero_Crusader nodeHeroTitle;
            class Crusader_buff nodeBuff;
            class Crusader_debuff nodeDebuff;
        end
        
        subgraph sgraph_ManatArms[ ]
            direction TB
            
            hero_ManatArms@{ shape: docs, label: "Man_at_Arms<br>#9876;#9876;#9876; #8982;"}
            %% hero_ManatArms([Man-at-Arms<br>#9876;#9876;#9876; #8982;])
            ManatArms_buff@{ shape: procs, label: "+++acc,crit<br>++prot,dmg<br>+++dod,<br>---stress"}
            ManatArms_debuff@{ shape: procs, label: "---dod,<br>---spd<br>-dmg"}
            hero_ManatArms ---> ManatArms_buff & ManatArms_debuff
            
            class hero_ManatArms nodeHeroTeam;
            class ManatArms_buff nodeBuff;
            class ManatArms_debuff nodeDebuff;
        end
        
        subgraph sgraph_Shieldbreaker[ ]
            direction TB
            
            hero_Shieldbreaker([#9022; <br>Shieldbreaker<br>#9876;#9876; #8982;#8982;])
            Shieldbreaker_buff@{ shape: procs, label: "(SELF)<br>+spd"}
            Shieldbreaker_debuff@{ shape: procs, label: "-spd<br>-stealth"}
            hero_Shieldbreaker ---> Shieldbreaker_buff & Shieldbreaker_debuff
        
            class hero_Shieldbreaker nodeHeroTitle;
            class Shieldbreaker_buff nodeSelfBuff;
            class Shieldbreaker_debuff nodeDebuff;
        end
        
        subgraph sgraph_Hellion[ ]
            direction TB
            
            hero_Hellion([Hellion<br>#9876;#9876;#9876;#9876;])
            Hellion_buff@{ shape: procs, label: "(SELF)<br>+dmg,acc"}
            Hellion_debuff@{ shape: procs, label: " "}
            hero_Hellion ---> Hellion_buff & Hellion_debuff
        
            class hero_Hellion nodeHeroTitle;
            class Hellion_buff nodeSelfBuff;
            class Hellion_debuff nodeDebuff;
        end
        
        subgraph sgraph_Jester[ ]
            direction TB
            
            hero_Jester@{ shape: docs, label: "__Jester__<br>#9876;#9876;#9876; #8982;"}
            %% Jester_buff@{ shape: procs, label: "+++acc,spd,<br>+++crit<br>--stress<br><i>FINALE:</i>-dod,spd,+stress(self)"}
            Jester_buff@{ shape: procs, label: "+++acc,spd,<br>+++crit<br>--stress<br><i>FINALE:</i>"}
            Jester_debuff@{ shape: procs, label: " "}
            hero_Jester ---> Jester_buff & Jester_debuff
        
            class hero_Jester nodeHeroTeam;
            class Jester_buff nodeBuff;
            class Jester_debuff nodeDebuff;
        end
        
        subgraph sgraph_Hwyman[ ]
            direction TB
            
            hero_Hwyman([#9022; <br>Highwayman<br>#9876;#9876; #8982;#8982;])
            Hwyman_buff@{ shape: procs, label: "(SELF)<br>+acc,crit,dmg<br>++crit<br>-dmg"}
            Hwyman_debuff@{ shape: procs, label: "-stealth"}
            hero_Hwyman ---> Hwyman_buff & Hwyman_debuff
        
            class hero_Hwyman nodeHeroTitle;
            class Hwyman_buff nodeSelfBuff;
            class Hwyman_debuff nodeDebuff;
        end
        
        subgraph sgraph_Leper[ ]
            direction TB
            
            hero_Leper([Leper<br>#9876;#9876;#9876; #8982;])
            Leper_buff@{ shape: procs, label: "(SELF)<br>+acc,dmg,crit<br>+prot,resist<br>-stress"}
            Leper_debuff@{ shape: procs, label: "-dmg,spd"}
            hero_Leper ---> Leper_buff & Leper_debuff
        
            class hero_Leper nodeHeroTitle;
            class Leper_buff nodeSelfBuff;
            class Leper_debuff nodeDebuff;
        end
        
        %% declare special actions here
        %% de_stealth>de_stealth]
        knock>knock]
        mark>mark] ~~~ stun>stun] ~~~ blight>blight] ~~~ bleed>bleed]
        pull>pull]
        shuffle>shuffle]
        
        %% css styling skill nodes %%
        class knock nodeSkillPlain;
        class stun nodeStun;
        class mark nodeMark;
        class pull nodePull;
        class blight nodeBlight;
        class shuffle nodeShuffle;
        class bleed nodeBleed;
        
        
        %% below are mappings heroes <-> actions here
        
        sgraph_Leper ---|#8680;3| knock
        
        riposte --- sgraph_Hwyman
        sgraph_Hwyman _bleed_1@o--o bleed
        
        sgraph_Abomination _blight_1@o--o blight
        sgraph_Abomination _stun_1@o--o stun
        
        cure _cure_1@--o sgraph_Doctor
        sgraph_Doctor _blight_2@o--o blight
        sgraph_Doctor _bleed_2@o--o bleed
        sgraph_Doctor _stun_2@o--o stun
        sgraph_Doctor _shuffle_1@o--o shuffle
        
        sgraph_Occultist _stun_3@-.-|front| stun
        sgraph_Occultist _mark_1@o--o mark
        sgraph_Occultist _pull_1@o--o pull
        
        sgraph_BountyHunter _bleed_3@o--o bleed
        sgraph_BountyHunter _mark_2@o--o mark
        sgraph_BountyHunter _pull_2@o--o pull
        sgraph_BountyHunter _stun_4@o--o stun
        sgraph_BountyHunter o--o knock
        sgraph_BountyHunter _shuffle_2@o--o shuffle
        
        cure _cure_2@-.-o|cure:<br>self| sgraph_GraveRobber
        %% stealth ---|self_<br>+++dmg,<br>+crit,dod| sgraph_GraveRobber
        sgraph_GraveRobber _blight_3@o--o blight
        
        guard _guard_1@--- sgraph_HoundMaster
        sgraph_HoundMaster _bleed_4@o--o bleed
        sgraph_HoundMaster _mark_3@o--o mark
        sgraph_HoundMaster _stun_5@o--o stun
        
        sgraph_Arbalest _mark_4@o--o mark
        
        %% mark _mark_5@o--o sgraph_Musketeer 
        %% sgraph_Musketeer o--o knock
        
        sgraph_Antiquarian _blight_4@-.- blight
        
        sgraph_Vestal _stun_6@o--o stun
        
        sgraph_Crusader _stun_7@o--o stun
        
        riposte --- sgraph_ManatArms
        guard _guard_2@---|self_+prot| sgraph_ManatArms
        %% sgraph_ManatArms _mark_6@o-.-o|passive| mark
        sgraph_ManatArms _stun_8@o--o|#8680;1| stun
        sgraph_ManatArms _shuffle_3@o--o shuffle
        
        pull _pull_3@--o sgraph_Shieldbreaker 
        sgraph_Shieldbreaker _blight_5@o--o blight
        
        cure _cure_3@-.-o|cure:<br>self| sgraph_Hellion
        stun _stun_9@-.-o|self-debuff| sgraph_Hellion
        sgraph_Hellion _bleed_5@o--o bleed
        
        sgraph_Jester _bleed_6@o--o bleed
        
        
        %% styling as more edges are added numerically
        class _guard_1,_guard_2,_guard_3,_guard_4,_guard_5 edgeGuard;
        class _shuffle_1,_shuffle_2,_shuffle_3,_shuffle_4,_shuffle_5 edgeShuffle;
        class _cure_1,_cure_2,_cure_3,_cure_4,_cure_5 edgeCure;
        class _blight_1,_blight_2,_blight_3,_blight_4,_blight_5 edgeBlight;
        class _stun_1,_stun_2,_stun_3,_stun_4,_stun_5,_stun_6,_stun_7,_stun_8,_stun_9,_stun_10 edgeStun;
        class _bleed_1,_bleed_2,_bleed_3,_bleed_4,_bleed_5,_bleed_6,_bleed_7,_bleed_8 edgeBleed;
        class _mark_1,_mark_2,_mark_3,_mark_4,_mark_5,_mark_6,_mark_7,_mark_8 edgeMark;
        class _pull_1,_pull_2,_pull_3,_pull_4,_pull_5 edgePull;
        
        %% format curve type for some links between heroes <-> actions to prettify the diagram
        _stun_1@{ curve: linear }
        _stun_2@{ curve: linear }
        _stun_3@{ curve: linear }
        _stun_4@{ curve: linear }
        _stun_5@{ curve: basis }
        _stun_6@{ curve: basis }
        _mark_1@{ curve: linear }
        _mark_2@{ curve: linear }
        _mark_3@{ curve: linear }
        _mark_4@{ curve: linear }
        %% _mark_5@{ curve: linear }
        %% _mark_6@{ curve: linear }
        %% _pull_1@{ curve: step }
        %% _pull_2@{ curve: step }
        _blight_1@{ curve: catmullRom }
        _blight_2@{ curve: catmullRom }
        _blight_3@{ curve: linear }
        _blight_4@{ curve: step }
        _blight_5@{ curve: linear }
        _bleed_1@{ curve: linear }
        _bleed_2@{ curve: linear }
        _bleed_3@{ curve: linear }
        _bleed_4@{ curve: linear }
        _cure_1@{ curve: linear }
        _cure_2@{ curve: basis }
        _cure_3@{ curve: linear }
    end
    
    %% styling hero subgraphs outside here
    class sgraph_Abomination sgraphHeroHealSelf;
    class sgraph_Doctor sgraphHeroHealSml;
    class sgraph_Occultist sgraphHeroHealBleed;
    class sgraph_Leper sgraphHeroHealSelf;
    class sgraph_Hwyman sgraphHeroPlain;
    class sgraph_BountyHunter sgraphHeroPlain;
    class sgraph_GraveRobber sgraphHeroPlain;
    class sgraph_HoundMaster sgraphHeroHealSelf;
    class sgraph_Arbalest sgraphHeroHeal;
    %% class sgraph_Musketeer sgraphHeroHeal;
    class sgraph_Antiquarian sgraphHeroHealSml;
    class sgraph_Vestal sgraphHeroHeal;
    class sgraph_Crusader sgraphHeroHeal;
    class sgraph_ManatArms sgraphHeroPlain;
    class sgraph_Shieldbreaker sgraphHeroArmorPierce;
    class sgraph_Hellion sgraphHeroArmorPierce;
    class sgraph_Jester sgraphHeroFinale;
    
    
    subgraph _affects_[afflicted]
        
        blighted{{blighted}}
        bled{{bled}}
    
        stunned{{stunned}}
        marked{{marked}}
        scrambled{{scrambled #8633;}}
        moved_fwd{{moved #8678;}}
        moved_bck{{moved #8680;}}
        
        %% css styling nodes %%
        class blighted nodeBlight;
        class bled nodeBleed;
        class stunned nodeStun;
        class marked nodeMark;
        class moved_bck nodeShuffle;
        class moved_fwd nodeShuffle;
        class scrambled nodeShuffle;
        
        
        %% mapping actions -> afflictions
        blight _blight_0@-.-> blighted
        bleed _bleed_0@-.-> bled
        stun _stun_0@-.-> stunned
        mark _mark_0@-.-> marked
        shuffle _shuffle_0@-.-> scrambled
        pull _pull_0@-.-> moved_fwd
        knock -.-> moved_bck
    end
    
    
    subgraph _benefits_[ ]
        
        _na([benefits:])
    
        _Hwyman([#9022; <br>Highwayman])
        _BountyHunter([#9022; #9022; #9022; <br>BountyHunter])
        %% _HoundMaster([#9022; #9022; <br>HoundMaster])
        _HoundMaster@{ shape: docs, label: "#9022; #9022; <br>HoundMaster"}
        _GraveRobber([#9022; #9022; #9022; <br>GraveRobber])
        _Arbalest([#9022; #9022; <br>Arbalest/<br>Musketeer])
        %% _Musketeer([#9022; #9022; <br>Musketeer])
        _Shieldbreaker([#9022; <br>Shieldbreaker])
        
        _GraveRobber ~~~ _BountyHunter
        _na ~~~  _BountyHunter & _Shieldbreaker 
        
        %% css styling hero nodes %%
        class _HoundMaster nodeHeroTeam;
        class _Arbalest nodeHeal;
        class _Hwyman nodeHeroPlain
        class _BountyHunter nodeHeroPlain
        class _GraveRobber nodeHeroPlain
        class _Shieldbreaker nodeHeroArmorPierce
        
        
        %% setting what afflictions benefit what heroes
        moved_bck ~~~ _na
        blighted _blight_101@---o|+| _GraveRobber
        stunned _stun_101@-..-o|+| _BountyHunter
        marked _mark_101@-.-o|+| _Hwyman
        marked _mark_102@---o|+<br>+<br>+| _BountyHunter
        marked _mark_103@-.-o|+| _GraveRobber
        marked _mark_104@---o|+<br>+| _HoundMaster
        marked _mark_105@---o|+<br>+| _Arbalest
        marked _mark_106@-.-o|+<br>+| _Shieldbreaker
        %% marked _mark_107@---o|+<br>+| _Musketeer
        %% bled _bleed_101@---o|+<br>+| _HoundMaster
        
        %% styling
        class _pull_0 edgePull;
        class _shuffle_0 edgeShuffle;
        class _blight_0,_blight_101 edgeBlight;
        class _bleed_0,_bleed_101 edgeBleed;
        class _stun_0,_stun_101 edgeStun;
        class _mark_0,_mark_101,_mark_102,_mark_103,_mark_104,_mark_105,_mark_106,_mark_107,_mark_108 edgeMark;
    end
    
```



